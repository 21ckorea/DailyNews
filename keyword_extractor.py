"""
keyword_extractor.py
--------------------
검색어(query)로부터 관련 인기 키워드를 동적으로 추출합니다.
API 키 불필요, 완전 무료로 동작합니다.

방식 (우선순위 순):
  1. Google 자동완성 (suggestqueries.google.com) — 빠르고 안정적
  2. pytrends Google Trends 연관검색어               — 실제 검색량 기반
  두 결과를 합산, 중복 제거 후 candidate_keywords로 반환합니다.

지원 패턴:
  - "DB계열사"   → "DB그룹", "DB계열사" 등으로 검색 → 연관 키워드 추출
  - "IT업계동향" → "IT", "IT업계" 등으로 검색 → 연관 인기 키워드 추출
  - 그 외        → 입력 그대로 검색하여 연관 키워드 추출
"""

import re
import time
import json
import requests
from urllib.parse import quote

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("[KeywordExtractor] ⚠️  pytrends 미설치. pip install pytrends 실행 필요.")


# ---------------------------------------------------------------------------
# 쿼리 패턴 감지
# ---------------------------------------------------------------------------

def _detect_query_type(query: str) -> str:
    """
    쿼리 유형을 분류합니다.
      - 'affiliate' : '*계열사' 패턴
      - 'trend'     : '업계동향', '트렌드', '인기', '순위' 등
      - 'general'   : 그 외
    """
    q = query.strip()
    if re.search(r'계열사', q):
        return 'affiliate'
    if re.search(r'동향|트렌드|인기|급상승|랭킹|순위|top\s*\d+', q, re.IGNORECASE):
        return 'trend'
    return 'general'


def _build_search_terms(query: str, query_type: str) -> list:
    """
    쿼리 타입별로 실제 검색에 사용할 검색어 목록을 반환합니다.
    순서대로 검색하며 결과를 합산합니다.
    """
    if query_type == 'affiliate':
        group = re.sub(r'\s*계열사.*', '', query).strip()
        return [f"{group}그룹", f"{group}계열사"]

    elif query_type == 'trend':
        industry = re.sub(r'\s*(업계동향|업계|동향|트렌드|인기|급상승|랭킹|순위).*', '', query).strip()
        terms = [industry, f"{industry}업계"]
        if query not in terms:
            terms.append(query)
        return terms

    else:
        return [query]


def _build_base_query(query: str, query_type: str) -> str:
    """config의 base_query 값으로 사용할 핵심 검색어를 반환합니다."""
    if query_type == 'affiliate':
        group = re.sub(r'\s*계열사.*', '', query).strip()
        return f"{group}그룹"
    elif query_type == 'trend':
        return re.sub(r'\s*(업계동향|업계|동향|트렌드|인기|급상승|랭킹|순위).*', '', query).strip()
    return query


# ---------------------------------------------------------------------------
# 소스 1: Google 자동완성 (suggestqueries)
# ---------------------------------------------------------------------------

def _fetch_google_autocomplete(keyword: str, headers: dict) -> list:
    """
    Google 자동완성 API에서 연관 검색어를 추출합니다.
    API 키 불필요. 실제 구글 검색창 자동완성 데이터를 반환합니다.
    """
    results = []
    try:
        url = (
            f"https://suggestqueries.google.com/complete/search"
            f"?client=firefox&hl=ko&gl=KR&q={quote(keyword)}"
        )
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = json.loads(resp.text)
        # 응답: [원본쿼리, [연관검색어1, 연관검색어2, ...]]
        suggestions = data[1] if len(data) > 1 and isinstance(data[1], list) else []
        results = [s.strip() for s in suggestions if s.strip()]

    except Exception as e:
        print(f"    ⚠️  Google 자동완성 오류 [{keyword}]: {e}")

    return results


# ---------------------------------------------------------------------------
# 소스 2: Google Trends (pytrends) 연관 검색어
# ---------------------------------------------------------------------------

def _fetch_google_trends(keyword: str, timeframe: str = 'now 7-d') -> list:
    """
    Google Trends의 연관 검색어(related queries)를 추출합니다.
    지난 7일간 가장 많이 함께 검색된 키워드를 반환합니다.
    pytrends 429 오류 시 조용히 빈 리스트 반환합니다.
    """
    if not PYTRENDS_AVAILABLE:
        return []

    results = []
    try:
        pytrends = TrendReq(hl='ko', tz=540, timeout=(5, 20))
        pytrends.build_payload([keyword], timeframe=timeframe, geo='KR')
        related = pytrends.related_queries()
        kw_data = related.get(keyword, {})

        # Top (인기 연관 검색어) — 검색량 높은 순
        top_df = kw_data.get('top')
        if top_df is not None and not top_df.empty:
            results.extend(top_df['query'].tolist())
            print(f"    ✅ Google Trends top {len(top_df)}개")

        # Rising (급상승 연관 검색어)
        rising_df = kw_data.get('rising')
        if rising_df is not None and not rising_df.empty:
            results.extend(rising_df['query'].tolist())
            print(f"    ✅ Google Trends rising {len(rising_df)}개")

    except Exception as e:
        # 429 등 오류는 조용히 무시 (Google 자동완성이 메인 소스)
        err_str = str(e)
        if '429' in err_str:
            print(f"    ℹ️  Google Trends 일시 차단 (429) — 자동완성 결과만 사용")
        else:
            print(f"    ⚠️  Google Trends 오류 [{keyword}]: {e}")

    return results


# ---------------------------------------------------------------------------
# 메인 클래스
# ---------------------------------------------------------------------------

class KeywordExtractor:
    """
    검색어(query)를 입력받아 관련 인기 키워드를 자동으로 추출합니다.
    API 키 불필요. Google 자동완성 + Google Trends를 조합합니다.

    사용 예:
        extractor = KeywordExtractor(config)

        result = extractor.extract("DB계열사")
        # → {"name": "DB계열사", "base_query": "DB그룹",
        #    "candidate_keywords": ["db그룹 계열사", "DB손해보험", ...]}

        result = extractor.extract("IT업계동향")
        # → {"name": "IT업계동향", "base_query": "IT",
        #    "candidate_keywords": ["삼성전자", "카카오", "네이버", ...]}
    """

    def __init__(self, config: dict):
        self.config = config
        self.top_n = config.get('ai', {}).get('trend_top_n', 100)
        self.delay = config.get('ai', {}).get('request_delay', 1.0)
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def extract(self, query: str) -> dict:
        """
        검색어로부터 카테고리 딕셔너리를 생성합니다.

        Args:
            query: 사용자 입력 검색어 (예: "DB계열사", "IT업계동향")

        Returns:
            {
                "name": str,
                "base_query": str,
                "candidate_keywords": List[str]  # 인기 순 정렬
            }
        """
        query = query.strip()
        query_type = _detect_query_type(query)
        search_terms = _build_search_terms(query, query_type)
        base_query = _build_base_query(query, query_type)

        print(f"\n[KeywordExtractor] ▶ 쿼리: '{query}' (타입: {query_type})")
        print(f"[KeywordExtractor]   검색어 목록: {search_terms}")

        all_keywords = []
        seen = set()

        # 불필요한 내비게이션/트랜잭션 검색어 필터링 (뉴스 검색에 부적합)
        stop_words_pattern = r'홈페이지|조회|채용|연봉|등록|고객센터|다운로드|전화번호|주가|주식|전망|디시|마이너|인벤|루리웹|블라인드|이용자|순위|근황|현실'

        def _add_unique(kws: list):
            """중복 없이 키워드 추가 (대소문자 무시, 뉴스 부적합 키워드 필터링)"""
            for kw in kws:
                kw = kw.strip()
                norm = kw.lower()
                # 뉴스에 부적합한 단어 필터링
                if kw and norm not in seen and len(kw) > 1:
                    if not re.search(stop_words_pattern, kw, re.IGNORECASE):
                        seen.add(norm)
                        all_keywords.append(kw)

        # 원본 검색어를 항상 1순위로 포함 (가장 관련성 높은 기사 확보)
        _add_unique([query])

        for i, term in enumerate(search_terms):
            print(f"\n  [{i+1}/{len(search_terms)}] 검색어: '{term}'")

            # ① Google 자동완성 (빠름, 안정적, API 키 불필요)
            print(f"    → Google 자동완성 호출...")
            google_ac = _fetch_google_autocomplete(term, self.headers)
            print(f"    ✅ Google 자동완성 {len(google_ac)}개: {google_ac[:6]}"
                  f"{'...' if len(google_ac) > 6 else ''}")
            _add_unique(google_ac)

            # ② Google Trends 연관검색어 (실제 검색량 기반, 선택적)
            print(f"    → Google Trends 연관검색어 호출...")
            trends_kws = _fetch_google_trends(term)
            if trends_kws:
                print(f"       샘플: {trends_kws[:5]}")
            _add_unique(trends_kws)

            # 요청 간 대기 (Rate Limit 방지)
            if i < len(search_terms) - 1:
                time.sleep(self.delay)

        total = len(all_keywords)
        final_keywords = all_keywords[:self.top_n]

        print(f"\n[KeywordExtractor] ✅ 추출 완료: 총 {total}개 → {len(final_keywords)}개 사용")
        print(f"[KeywordExtractor]   키워드: {final_keywords[:15]}"
              f"{'...' if len(final_keywords) > 15 else ''}")

        return {
            'name': query,
            'base_query': base_query,
            'candidate_keywords': final_keywords,
        }

    def extract_multiple(self, queries: list) -> list:
        """
        여러 검색어를 순서대로 처리합니다.

        Args:
            queries: 검색어 리스트

        Returns:
            카테고리 딕셔너리 리스트 (실패한 쿼리는 건너뜀)
        """
        results = []
        for idx, query in enumerate(queries):
            try:
                category = self.extract(query)
                results.append(category)
                if idx < len(queries) - 1:
                    time.sleep(self.delay)
            except Exception as e:
                print(f"[KeywordExtractor] ❌ '{query}' 처리 실패: {e}")
        return results


# ---------------------------------------------------------------------------
# 독립 실행 테스트
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import yaml

    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    extractor = KeywordExtractor(config)

    test_queries = ["DB계열사", "IT업계동향", "반도체"]

    for q in test_queries:
        print(f"\n{'='*60}")
        result = extractor.extract(q)
        print(f"\n최종 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"{'='*60}")
        time.sleep(2)
