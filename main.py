import os
import yaml
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader
from apscheduler.schedulers.blocking import BlockingScheduler
from crawler import NewsCrawler
from mailer import Mailer
from keyword_extractor import KeywordExtractor

# Define KST timezone (UTC+9)
KST = timezone(timedelta(hours=9))

def job(query_override: list = None, static_categories: list = None):
    """
    Args:
        query_override: 동적 검색어 리스트. 예: ["보험개발원"]
        static_categories: config.yaml에서 그대로 사용할 카테고리명 리스트. 예: ["DT신기술", "IT업계동향"]
                           둘 다 None이면 config.yaml의 전체 categories를 그대로 사용.
    """
    now_kst = datetime.now(KST)
    print(f"[{now_kst.strftime('%Y-%m-%d %H:%M:%S')}] Starting Daily News Job...")
    
    try:
        # 1. Initialize
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 2. 카테고리 믹스 로직
        mailing_groups = config.get('mailing_groups', [])
        
        if query_override is not None or static_categories is not None:
            # Override Mode (Manual run)
            final_categories = []
            if query_override:
                print(f"\n[Dynamic Mode] 동적 검색어: {query_override}")
                extractor = KeywordExtractor(config)
                dynamic_categories = extractor.extract_multiple(query_override)
                if dynamic_categories: final_categories.extend(dynamic_categories)
            
            if static_categories:
                print(f"\n[Static Mode] 유지할 기존 카테고리: {static_categories}")
                for static_name in static_categories:
                    cat = next((c for c in config.get('categories', []) if c['name'] == static_name), None)
                    if cat:
                        final_categories.append(cat)
                        print(f"  - [{cat['name']}] (정적) 키워드 {len(cat.get('candidate_keywords', []))}개")
            
            config['categories'] = final_categories or config['categories']
            groups_to_send = [{"name": "Manual Run", "recipients": [], "categories": [c['name'] for c in config['categories']]}]
            # Collect all recipients from all groups for manual run
            all_recipients = []
            for g in mailing_groups: all_recipients.extend(g.get('recipients', []))
            groups_to_send[0]['recipients'] = list(set(all_recipients))
        else:
            # Normal Mode (Multi-group)
            required_cat_names = set()
            for group in mailing_groups:
                required_cat_names.update(group.get('categories', []))
            
            print(f"\n[Multi-Group Mode] 총 {len(required_cat_names)}개 카테고리 통합 수집 시작")
            config['categories'] = [c for c in config.get('categories', []) if c['name'] in required_cat_names]
            groups_to_send = mailing_groups

        if not config['categories']:
            print("[Warning] 수집할 카테고리가 없습니다.")
            return

        crawler = NewsCrawler(config)
        mailer = Mailer(config)
        
        # 3. Fetch News (Once for all unique categories)
        results, keywords_map, ranked_keywords_map, scores_map = crawler.get_all_news()
        
        # 4. Distribute to each mailing group
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('news_template.html')
        
        for group in groups_to_send:
            group_name = group['name']
            recipients = group['recipients']
            group_cats = group['categories']
            
            print(f"\n[{group_name}] 뉴스레터 구성 중... (카테고리 순서: {group_cats})")
            
            # Filter and RE-ORDER data for this group based on group_cats
            group_results = {}
            group_keywords = {}
            group_all_keywords = {}
            group_scores = {}
            
            for cat in group_cats:
                if cat in results:
                    group_results[cat] = results[cat]
                    group_keywords[cat] = keywords_map.get(cat, [])
                    group_all_keywords[cat] = ranked_keywords_map.get(cat, [])
                    group_scores[cat] = scores_map.get(cat, {})
            
            if not group_results:
                print(f"  - [{group_name}] 보낼 기사가 없어 건너뜜")
                continue

            html_content = template.render(
                group_name=group_name,
                results=group_results,
                keywords_map=group_keywords,
                all_keywords_map=group_all_keywords,
                scores_map=group_scores,
                today=now_kst.strftime("%Y/%m/%d %H:%M")
            )
            
            # 5. Send Email
            subject = f"[Daily News] {now_kst.strftime('%Y-%m-%d')} 뉴스레터 ({group_name})"
            mailer.send_email(subject, html_content, recipients=recipients)
        
        print(f"\n[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] All jobs finished successfully.")
        
    except Exception as e:
        import traceback
        print(f"Error during job execution: {e}")
        traceback.print_exc()

import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Daily News Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # config.yaml 파일 그대로 실행
  python main.py --run-once

  # 동적 검색어만 실행
  python main.py --run-once --query "DB계열사"

  # config.yaml의 기존 내용 중 일부 + 동적 검색어 조합
  python main.py --run-once --query "보험개발원" --static "DT신기술,IT업계동향"
        """
    )
    parser.add_argument('--run-once', action='store_true',
                        help="Run the job exactly once and exit (for crontab)")
    parser.add_argument('--query', type=str, default=None,
                        help="동적 키워드 추출 검색어. 쉼표(,)로 여러 개 지정 가능.")
    parser.add_argument('--static', type=str, default=None,
                        help="config.yaml에서 그대로 사용할 카테고리 이름. 쉼표(,)로 지정.")
    args = parser.parse_args()

    # 파싱: 쉼표 구분 → 리스트
    query_list = None
    if args.query:
        query_list = [q.strip() for q in args.query.split(',') if q.strip()]
        
    static_list = None
    if args.static:
        static_list = [q.strip() for q in args.static.split(',') if q.strip()]

    if args.run_once:
        print(f"Running in 'run-once' mode.")
        job(query_override=query_list, static_categories=static_list)
        return

    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    schedule_time = config.get('settings', {}).get('schedule_time', '08:00')
    hour, minute = schedule_time.split(':')
    
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'cron', hour=hour, minute=minute)
    
    print(f"Daily News System started. Scheduled for {schedule_time} daily.")
    
    # Run once immediately for testing (optional, comment out for production)
    job()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
