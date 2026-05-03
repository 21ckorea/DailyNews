import os
import yaml
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader
from apscheduler.schedulers.blocking import BlockingScheduler
from crawler import NewsCrawler
from mailer import Mailer

# Define KST timezone (UTC+9)
KST = timezone(timedelta(hours=9))

def job():
    now_kst = datetime.now(KST)
    print(f"[{now_kst.strftime('%Y-%m-%d %H:%M:%S')}] Starting Daily News Job...")
    
    try:
        # 1. Initialize
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        crawler = NewsCrawler(config)
        mailer = Mailer(config)
        
        # 2. Fetch News
        results, keywords_map = crawler.get_all_news()
        
        # 3. Render HTML
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('news_template.html')
        
        html_content = template.render(
            results=results,
            keywords_map=keywords_map,
            today=now_kst.strftime("%Y/%m/%d %H:%M")
        )
        
        # 4. Send Email
        subject = f"[Daily News] {now_kst.strftime('%Y-%m-%d')} 뉴스레터"
        mailer.send_email(subject, html_content)
        
        print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] Job finished successfully.")
        
    except Exception as e:
        print(f"Error during job execution: {e}")

def main():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    schedule_time = config['settings']['schedule_time']
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
