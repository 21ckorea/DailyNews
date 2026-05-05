import requests
from bs4 import BeautifulSoup
import re
import base64
from urllib.parse import urljoin, quote

def test_google_news_resolution(target_url, title):
    print(f"\n[STEP 1] Resolving Google News Tracker: {target_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://news.google.com/'
    }

    final_url = target_url
    is_decoded = False
    
    # Stage 1: Advanced Protobuf-like Base64 Decoding
    try:
        encoded_part = target_url.split('articles/')[1].split('?')[0]
        # Clean the base64 string
        padding = '=' * (4 - len(encoded_part) % 4)
        raw_data = base64.urlsafe_b64decode(encoded_part + padding)
        
        # Google News URLs are often preceded by a length byte or specific markers
        # We look for the first occurrence of "http" in the raw binary data
        url_start = raw_data.find(b'http')
        if url_start != -1:
            # Extract everything from 'http' to the next non-printable character
            potential_url = ""
            for byte in raw_data[url_start:]:
                if 32 <= byte <= 126: # Printable ASCII
                    potential_url += chr(byte)
                else:
                    break
            
            # Clean up trailing garbage common in protobuf-style strings
            if '?' in potential_url: potential_url = potential_url.split('?')[0]
            while potential_url and potential_url[-1] in '"\'.,)]}': potential_url = potential_url[:-1]
            
            if 'zdnet.co.kr' in potential_url:
                final_url = potential_url
                print(f"  - SUCCESS (Stage 1): Deciphered ZDNet URL: {final_url}")
                is_decoded = True
    except Exception as e:
        print(f"  - Stage 1 Decipher error: {e}")

    # Stage 2: Pattern Search in Raw Bytes (If Stage 1 failed to find "http" clearly)
    if not is_decoded:
        try:
            # Sometimes the URL is double-encoded or has a prefix like \x08\x1a
            # We search for any string containing 'zdnet.co.kr'
            matches = re.findall(rb'[a-z0-9.-]+\.zdnet\.co\.kr[^\s\x00-\x1f\x7f-\xff]*', raw_data)
            if matches:
                host_path = matches[0].decode('utf-8', errors='ignore')
                final_url = "https://" + host_path
                if '?' in final_url: final_url = final_url.split('?')[0]
                print(f"  - SUCCESS (Stage 2): Pattern matched ZDNet URL: {final_url}")
                is_decoded = True
        except: pass

    # Stage 3: Title-Based Reverse Search (Multi-Portal Fail-Safe)
    if not is_decoded:
        print("  - Stage 1 & 2 Failed. Using Stage 3: Multi-Portal Reverse Search...")
        # Refine title to increase search match rate
        refined_title = title.split(',')[0].split('...')[0].strip()
        if len(refined_title) < 10: refined_title = title[:30]
        
        search_portals = [
            f"https://search.daum.net/search?w=news&q={quote(refined_title)}",
            f"https://search.naver.com/search.naver?where=news&query={quote(refined_title)}"
        ]
        
        for search_url in search_portals:
            try:
                print(f"  - Searching: {search_url}")
                search_resp = requests.get(search_url, headers=headers, timeout=10)
                search_soup = BeautifulSoup(search_resp.text, 'html.parser')
                
                # Check Daum/Naver links
                potential_links = search_soup.select('.item-title a, .news_tit')
                for item in potential_links:
                    link = item.get('href')
                    if any(domain in link for domain in ['g-enews.com', 'zdnet.co.kr', 'v.daum.net', 'n.news.naver.com']):
                        final_url = link
                        print(f"  - SUCCESS (Stage 3): Found matched URL: {final_url}")
                        is_decoded = True
                        break
                if is_decoded: break
            except: pass

    if not is_decoded:
        print("  - FAILED to resolve valid Article URL. Aborting test.")
        return

    print(f"\n[STEP 2] Extracting image from: {final_url}")
    try:
        headers['Referer'] = 'https://zdnet.co.kr/'
        response = requests.get(final_url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Priority 1: OG Image (Filter out Ads)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            print(f"  - Detected OG Image: {img_url}")
            if 'adv.zdnet.co.kr' in img_url or 'RealMedia' in img_url:
                print("    ! IGNORED: This is an AD image.")
            else:
                print("    * SUCCESS: This is a valid article image.")
                # We still continue to check body images to compare
        
        # Priority 2: Body Image (The "Article Body" Scan)
        print("\n[STEP 3] Scanning Article Body for Images...")
        body_selectors = ['.view_body', '#article-view-content-div', '#articleBodyContents', 'article']
        found_images = []
        
        for selector in body_selectors:
            container = soup.select_one(selector)
            if container:
                print(f"  - Found container: {selector}")
                for img in container.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src:
                        src = urljoin(final_url, src)
                        if src.startswith('//'): src = 'https:' + src
                        
                        # THE CRITICAL FILTER: Ignore known ad patterns
                        is_ad = any(p in src.lower() for p in ['adv.', 'realmedia', 'ad.', 'banner', 'pixel'])
                        status = "[AD]" if is_ad else "[ARTICLE]"
                        print(f"    {status} {src}")
                        
                        if not is_ad:
                            found_images.append(src)
        
        if found_images:
            print(f"\n[FINAL RESULT] Best Image Selected: {found_images[0]}")
            if found_images[0] == "https://image.zdnet.co.kr/2021/06/03/4c84914926f56cdf6b15283e3c507b65.jpg":
                print("!!! CONGRATULATIONS! MATCHED THE EXPECTED ANSWER !!!")
            else:
                print("... Still not the expected one. Need more refinement.")
        else:
            print("\n[FINAL RESULT] No valid article image found.")

    except Exception as e:
        print(f"  - Extraction error: {e}")

if __name__ == "__main__":
    # Test Case 1: ZDNet (Samsung)
    # test_url = "https://news.google.com/rss/articles/CBMiVkFVX3lxTE1ET2NDT005alNQa0JBN0U5ZTZkZDJlVUpOT2VueHFSMzJveHpRZkRpc3BnUmNWYXlhNXNBazVSTVBBMkhMOUllN0Y0LXkwQ3BOZWgtVXRn?oc=5"
    # test_title = "삼성 파운드리 4나노 내년까지 '풀부킹'…하반기 흑자전환 시동"
    
    # Test Case 2: g-enews (Golf)
    test_url = "https://news.google.com/rss/articles/CBMiiwFBVV95cUxNcjU3ZEVnSEhWNDlHV19ta1J1QWdtWklIQ0R0VE9xYnVfV1B2X1VubzloWFcwWXdkc0o0OEJrVWhuNGxRWkdTLUx6Q3pHb3g3eC0wMWRSNDhtd1duUWxfOVVFX2pMNzFXN3VRZ0dmX29uSlFqNGVWdnByUXFRMHoyTXRjYTFFQmFOZXUw?oc=5"
    test_title = "골프계에 혁신을 주도하는 DB그룹, DB위민스 챔피언십, 코스에 마련한 '드라이빙 레인지' 눈길"
    
    test_google_news_resolution(test_url, test_title)
