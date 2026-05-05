import requests
import base64
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}
ad_patterns = ['adv.', 'realmedia', 'banner', 'pixel', 'spacer', 'vending']

test_urls = [
    ("기사1 (글로벌이코노믹 골프)",
     "https://news.google.com/rss/articles/CBMiiwFBVV95cUxNcjU3ZEVnSEhWNDlHV19ta1J1QWdtWklIQ0R0VE9xYnVfV1B2X1VubzloWFcwWXdkc0o0OEJrVWhuNGxSWkdTLUx6Q3pHb3g3eC0wMWRSNDhtd1duUWxfOVVFX2pMNzFXN3VRZ0dmX29uSlFqNGVWdnByUXFRMHoyTXRjYTFFQmFOZXUw?oc=5",
     "골프계에 혁신을 주도하는 DB그룹, DB위민스 챔피언십, 코스에 마련한 '드라이빙 레인지' 눈길"),
    ("기사2 (뉴스로드)",
     "https://news.google.com/rss/articles/CBMia0FVX3lxTE52SFdiMU9EY0t2VlN6WE1yY3N5dURiQ3ZHTUdHcENHaGhjSUU2bkhlNndYOE5KeFhUSEYwb19Rd0NwMzEwVGEwUEQ0MU1qVUw1VVd3RjFjX3EyaHBXME9UbTdKaHlLaWE1aGJR0gFvQVVfeXFMTjVtdHJfNkZQWHNZYUR5SkQ2dUdJM3A5MU9DYjhxcl8wT3BzYzVIRlBqSF9EX0pQZGVqQTItSHRUY0JSTU53NWRQUHlkZ1kwUEtjeFd4RElMQUhKNTNvRnM3bVppVGo0V0tacVJHY0U0?oc=5",
     "KLPGA투어 '변화(變化)'이끈 DB그룹, '제1회 DB위민스 챔피언십' 코스에 천연잔디 '드라이빙 레인지'"),
    ("기사3 (딜사이트)",
     "https://news.google.com/rss/articles/CBMiT0FVX3lxTFA3UFBuUmVIRlVMS2VEYmRTZ2RlaU1UVU9oOEFMNlBZZTdkVE43eGlTV2czUTJzU0lLTHdfcllVTVBJWHRReWxMT0tra19vN1U?oc=5",
     "[DB그룹 동곡재단] 흔들리는 창업주와 재단 가신들...세자의 반전기회"),
]

def try_binary_decode(url):
    try:
        encoded_part = url.split('articles/')[1].split('?')[0]
        padding = '=' * (4 - len(encoded_part) % 4)
        raw_data = base64.urlsafe_b64decode(encoded_part + padding)
        url_matches = re.findall(rb'https?://[^\s\x00-\x1f\x7f-\xff]+', raw_data)
        for match in url_matches:
            candidate = match.decode('utf-8', errors='ignore')
            candidate = candidate.split('\x00')[0].split('\x01')[0]
            if '?' in candidate: candidate = candidate.split('?')[0]
            while candidate and candidate[-1] in '"\'.,)]}': candidate = candidate[:-1]
            if all(d not in candidate for d in ['google.com', 'gstatic.com', 'angular.dev']):
                return candidate
    except: pass
    return None

def get_image(final_url):
    try:
        resp = requests.get(final_url, headers=headers, timeout=12, allow_redirects=True)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for prop in ['twitter:image', 'og:image', 'nate:image']:
            tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
            if tag:
                content = tag.get('content', '')
                valid = content and not any(p in content.lower() for p in ad_patterns)
                print(f"    [{prop}] {'✅' if valid else '❌ ad-filtered'} {content[:80]}")
                if valid: return content
        
        # Body fallback
        body_selectors = ['.view_body', '#articleBody', '#article-view-content-div',
                          '#articleBodyContents', 'article', '.article_view',
                          '.view_content', '.article-body', '.news_cont']
        for sel in body_selectors:
            container = soup.select_one(sel)
            if container:
                for img in container.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src:
                        src = urljoin(final_url, src)
                        if src.startswith('//'): src = 'https:' + src
                        if not any(p in src.lower() for p in ad_patterns):
                            print(f"    [body img via '{sel}'] ✅ {src[:80]}")
                            return src
        return None
    except Exception as e:
        print(f"    ❌ 요청 에러: {e}")
        return None

for name, google_url, title in test_urls:
    print(f"\n{'='*65}")
    print(f"[{name}]")
    print(f"제목: {title[:50]}")

    # Step 1: Binary decode
    decoded = try_binary_decode(google_url)
    print(f"  STEP1 이진해독: {'✅ ' + decoded if decoded else '❌ 실패'}")

    final_url = decoded

    # Step 2: Daum reverse search with title
    if not final_url and title:
        clean_kw = title.split(' - ')[0].split(' | ')[0].split(' : ')[0]
        if ',' in clean_kw:
            parts = [p.strip() for p in clean_kw.split(',')]
            clean_kw = max(parts, key=len)
        clean_kw = re.sub(r'[\'"\[\]]', '', clean_kw).strip()
        search_titles = [f'"{clean_kw}"', clean_kw[:25].strip()]

        for kw in search_titles:
            try:
                s_url = f"https://search.daum.net/search?w=news&q={quote(kw)}"
                s_resp = requests.get(s_url, headers=headers, timeout=10)
                s_soup = BeautifulSoup(s_resp.text, 'html.parser')
                links = s_soup.select('.item-title a, .tit_main, a.link_txt')
                for link_elem in links:
                    href = link_elem.get('href', '')
                    if href.startswith('http') and any(d in href for d in ['v.daum.net', 'news.', 'view.', 'article', 'g-enews.com', 'newsroad.co.kr', 'dealsite.co.kr']):
                        final_url = href
                        print(f"  STEP2 Daum역추적: ✅ '{kw[:30]}' → {href}")
                        break
                if final_url: break
            except Exception as e:
                print(f"  STEP2 Daum역추적 에러: {e}")
                continue

        if not final_url:
            print(f"  STEP2 Daum역추적: ❌ 검색어 '{search_titles[0][:30]}' 결과 없음")

    if not final_url:
        print(f"  ❌ 최종 URL 없음 → 이미지 추출 불가")
        continue

    # Step 3: Extract image
    print(f"  STEP3 이미지 추출 from: {final_url}")
    img = get_image(final_url)
    print(f"  최종 결과: {'✅ ' + img[:80] if img else '❌ 이미지 없음'}")
