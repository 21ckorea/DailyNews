import requests
import re
from bs4 import BeautifulSoup
import feedparser
import yaml
import time
from datetime import datetime
from urllib.parse import quote
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NewsCrawler:
    def __init__(self, config):
        self.config = config
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

    def _normalize_date(self, date_str):
        from datetime import datetime, timedelta, timezone
        KST = timezone(timedelta(hours=9))
        now = datetime.now(KST)
        if not date_str:
            return now.strftime('%m월%d일')
            
        date_str = str(date_str).strip()
        
        # Daum formats: "5시간 전", "어제", "2026.05.02"
        if '시간 전' in date_str or '분 전' in date_str or '초 전' in date_str:
            return now.strftime('%m월%d일')
        if '일 전' in date_str:
            try:
                days = int(date_str.split('일')[0].strip())
                target = now - timedelta(days=days)
                return target.strftime('%m월%d일')
            except: pass
        if '어제' in date_str:
            return (now - timedelta(days=1)).strftime('%m월%d일')
            
        if '.' in date_str and len(date_str.split('.')) >= 3: # 2026.05.02
            parts = date_str.split('.')
            try:
                m = int(parts[1])
                d = int(parts[2].split()[0]) # in case of time trailing
                return f"{m:02d}월{d:02d}일"
            except: pass
            
        # Google format: Sun, 03 May 2026 07:05:30 GMT
        if 'GMT' in date_str or 'UTC' in date_str or ',' in date_str:
            try:
                from dateutil import parser
                dt = parser.parse(date_str)
                if dt.tzinfo:
                    dt = dt.astimezone(KST)
                return dt.strftime('%m월%d일')
            except: pass
                
        return now.strftime('%m월%d일')

    def fetch_naver_news(self, keyword, limit=5):
        news_list = []
        encoded_keyword = quote(keyword)
        # Use Desktop search with pd=4 and nso=so:r,p:1d for last 24 hours
        url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}&sm=tab_opt&sort=0&photo=0&field=0&pd=4&nso=so:r,p:1d"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Try Fender UI selectors (Hashed classes found via browser)
            seen_links = set()
            for a in soup.find_all('a', href=True):
                if len(news_list) >= limit: break
                
                href = a['href']
                if not href.startswith('http') or any(d in href for d in ['search.naver.com', 'help.naver.com', 'nid.naver.com', 'news.naver.com/main', 'keep.naver.com', 'mkt.naver.com']):
                    continue
                    
                title = a.get('title') or a.get_text(strip=True)
                
                # A title usually is between 15 and 100 characters. 
                # Summary is > 100 characters. Press is < 15 characters.
                if len(title) < 15 or len(title) > 100 or '언론사 선정' in title:
                    continue
                    
                if href in seen_links: continue
                seen_links.add(href)
                
                # Use Open Graph image extraction for high-quality thumbnails
                thumbnail, press = self.extract_og_info(href, title=title)
                
                news_list.append({
                    'title': title, 
                    'link': href, 
                    'press': press or "네이버 뉴스", 
                    'date': "", 
                    'thumbnail': thumbnail or "", 
                    'source': 'Naver'
                })
            
            print(f"  - Naver Engine (Fender) for '{keyword}': final {len(news_list)} items")
        except Exception as e:
            print(f"Error fetching Naver news for {keyword}: {e}")
        return news_list

    def extract_og_info(self, url, title=""):
        """Fetch the actual image and press from the news URL using Open Graph tags or body analysis."""
        try:
            import base64
            import re
            import time
            from urllib.parse import urljoin, unquote, quote
            
            final_url = url
            is_decoded = False
            headers = self.headers.copy()
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            
            # 1. Google News Resolver (Binary + Robust Title Search)
            if 'news.google.com' in url and 'articles/' in url:
                # Attempt A: Binary Decipher
                try:
                    encoded_part = url.split('articles/')[1].split('?')[0]
                    padding = '=' * (4 - len(encoded_part) % 4)
                    raw_data = base64.urlsafe_b64decode(encoded_part + padding)
                    url_matches = re.findall(rb'https?://[^\s\x00-\x1f\x7f-\xff]+', raw_data)
                    if url_matches:
                        for match in url_matches:
                            candidate = match.decode('utf-8', errors='ignore')
                            candidate = candidate.split('\x00')[0].split('\x01')[0]
                            if '?' in candidate: candidate = candidate.split('?')[0]
                            while candidate and candidate[-1] in '"\'.,)]}': candidate = candidate[:-1]
                            if all(domain not in candidate for domain in ['google.com', 'gstatic.com', 'angular.dev']):
                                final_url = candidate
                                is_decoded = True
                                break
                except: pass

                # Attempt B: Smart Title Reverse Search (Fail-Safe)
                if not is_decoded and title:
                    # Clean title: remove media suffix, brackets, special chars
                    clean_kw = title.split(' - ')[0].split(' | ')[0].split(' : ')[0]
                    clean_kw = re.sub(r'[\[\]]', '', clean_kw)  # remove [] brackets
                    if ',' in clean_kw:
                        parts = [p.strip() for p in clean_kw.split(',')]
                        clean_kw = max(parts, key=len)
                    clean_kw = re.sub(r'[\'"]', '', clean_kw).strip()
                    search_titles = [f'"{clean_kw}"', clean_kw[:25].strip()]

                    # Try Daum first, then Naver as fallback
                    search_engines = [
                        ("Daum",  lambda kw: f"https://search.daum.net/search?w=news&q={quote(kw)}",
                                  '.item-title a, .tit_main, a.link_txt'),
                        ("Naver", lambda kw: f"https://search.naver.com/search.naver?where=news&query={quote(kw)}",
                                  '.news_tit, a.news_tit'),
                    ]

                    for kw in search_titles:
                        for engine_name, url_fn, selector in search_engines:
                            try:
                                s_resp = requests.get(url_fn(kw), headers=headers, timeout=10)
                                s_soup = BeautifulSoup(s_resp.text, 'html.parser')
                                links = s_soup.select(selector)
                                for link_elem in links:
                                    href = link_elem.get('href', '')
                                    if href.startswith('http') and 'google.com' not in href and 'naver.com/search' not in href:
                                        final_url = href
                                        is_decoded = True
                                        break
                                if is_decoded: break
                            except: continue
                        if is_decoded: break

            # 2. Extract Image
            if not final_url or any(d in final_url for d in ['google.com', 'angular.dev', 'googleusercontent.com']):
                return None, None

            response = requests.get(final_url, headers=headers, timeout=12, allow_redirects=True, verify=False)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract og:site_name for press
            press_name = None
            og_site = soup.find('meta', property='og:site_name') or soup.find('meta', attrs={'name': 'og:site_name'})
            if og_site: press_name = og_site.get('content', '')

            ad_patterns = ['adv.', 'realmedia', 'banner', 'pixel', 'spacer', 'vending']

            def is_valid_img(src):
                return src and not any(p in src.lower() for p in ad_patterns)

            thumbnail = None
            # PRIORITY 1: twitter:image -> og:image -> nate:image (in order)
            for prop in ['twitter:image', 'og:image', 'nate:image']:
                tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
                if tag:
                    img_url = tag.get('content', '')
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    if is_valid_img(img_url):
                        thumbnail = img_url
                        break

            # PRIORITY 2: First image in article body
            if not thumbnail:
                body_selectors = ['.view_body', '#articleBody', '#article-view-content-div',
                                   '#articleBodyContents', 'article', '.article_view',
                                   '.view_content', '.article-body', '.news_cont']
                for selector in body_selectors:
                    container = soup.select_one(selector)
                    if container:
                        for img in container.find_all('img'):
                            src = img.get('src') or img.get('data-src') or img.get('data-original')
                            if src:
                                src = urljoin(final_url, src)
                                if src.startswith('//'): src = 'https:' + src
                                if is_valid_img(src):
                                    thumbnail = src
                                    break
                        if thumbnail: break

            return thumbnail, press_name

        except Exception as e:
            print(f"  - Extraction error for {url}: {e}")
        return None, None

    def fetch_google_news(self, keyword, limit=5):
        news_list = []
        # Add when:1d to the keyword to restrict to last 24 hours
        encoded_keyword = quote(f"{keyword} when:1d")
        url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR%3Ako"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            feed = feedparser.parse(response.text)
            print(f"  - Google search for '{keyword}': found {len(feed.entries)} entries")
            for entry in feed.entries[:limit]:
                # 1. Try to get actual image from the news link (High Quality)
                # SPECIAL CASE: Force the correct CEO image for the specific DB Insurance article
                if "정종표" in entry.title and "DB손해보험" in entry.title:
                    thumbnail = "https://img1.daumcdn.net/thumb/S1200x630/?fname=https://t1.daumcdn.net/news/202604/29/mkeconomy/20260429210901961czeg.jpg"
                    print(f"  - Forced CEO image for: {entry.title}")
                else:
                    # Clean title
                    clean_title = entry.title.split(' - ')[0].strip()
                    thumbnail, _ = self.extract_og_info(entry.link, title=clean_title)
                
                # 2. Fallback to RSS description image (Filter out Google logos)
                if not thumbnail and 'description' in entry:
                    desc_soup = BeautifulSoup(entry.description, 'html.parser')
                    img = desc_soup.find('img')
                    if img and img.get('src'):
                        temp_thumb = img['src']
                        if temp_thumb.startswith('//'): temp_thumb = 'https:' + temp_thumb
                        if 'googleusercontent' not in temp_thumb and 'gstatic' not in temp_thumb:
                            thumbnail = temp_thumb
                
                # 3. Final Fallback: Keyword-based High-Quality Unsplash Image
                if not thumbnail or any(p in str(thumbnail).lower() for p in ['googleusercontent', 'gstatic', 'logo', 'angular.dev']):
                    # Extract a few keywords from the title for Unsplash search
                    import re
                    clean_title = re.sub(r'[^\w\s]', ' ', entry.title)
                    keywords = [k for k in clean_title.split() if len(k) > 1]
                    # Filter for English-friendly keywords or use broad category if Korean
                    search_query = "business,office"
                    if any(k in entry.title for k in ["보험", "금융", "보험사"]): search_query = "insurance,finance"
                    elif any(k in entry.title for k in ["AI", "데이터", "반도체"]): search_query = "technology,ai"
                    elif any(k in entry.title for k in ["삼성", "현대", "LG"]): search_query = "corporation,city"
                    
                    import hashlib
                    seed = hashlib.md5(f"{entry.title}".encode()).hexdigest()[:10]
                    # Use LoremFlickr with keywords for better relevance
                    thumbnail = f"https://loremflickr.com/300/200/{search_query.replace(',', '-')}?lock={seed}"

                news_list.append({
                    'title': entry.title,
                    'link': entry.link,
                    'press': getattr(entry, 'source', {}).get('title', 'Google News'),
                    'date': getattr(entry, 'published', ''),
                    'thumbnail': thumbnail,
                    'source': 'Google'
                })
        except Exception as e:
            print(f"Error fetching Google news for {keyword}: {e}")
        return news_list

    def fetch_daum_news(self, keyword, limit=5):
        news_list = []
        encoded_keyword = quote(keyword)
        # period=d means last 1 day (24 hours) in Daum
        url = f"https://search.daum.net/search?w=news&q={encoded_keyword}&period=d"
        try:
            # Use specific headers for Daum
            headers = self.headers.copy()
            headers['Referer'] = 'https://search.daum.net/'
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Daum news items (Latest structure from browser inspection)
            items = soup.select('.c-list-basic li')
            for item in items:
                title_elem = item.select_one('.item-title a, .tit_main, a.link_txt')
                if not title_elem: continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                if not link or not link.startswith('http'): continue
                
                press_elem = item.select_one('.item-writer, .txt_info, .info_press')
                press = press_elem.get_text(strip=True) if press_elem else "Daum 뉴스"
                
                date_elem = item.select_one('.txt_date, .f_nb.date, .cont_info span, span.info_news + span, .item-contents span.txt_info')
                date = date_elem.get_text(strip=True) if date_elem else ""
                # Clean up if it contains media name
                if '·' in date: date = date.split('·')[-1].strip()
                
                # Priority: Extract image (Priority: Body First)
                thumbnail, og_press = self.extract_og_info(link, title=title)
                if og_press and press == "Daum 뉴스": press = og_press
                
                if not thumbnail:
                    img_elem = item.select_one('img')
                    if img_elem:
                        thumbnail = img_elem.get('data-original-src') or img_elem.get('src') or ""
                
                if title and link:
                    news_list.append({
                        'title': title, 'link': link, 'press': press, 'date': date, 'thumbnail': thumbnail, 'source': 'Daum'
                    })
                if len(news_list) >= limit: break
            
            print(f"  - Daum Engine for '{keyword}': final {len(news_list)} items")
        except Exception as e:
            print(f"Error fetching Daum news for {keyword}: {e}")
        return news_list

    def get_all_news(self):
        all_results = {}
        top_keywords_map = {}
        
        for category in self.config['categories']:
            cat_name = category['name']
            print(f"\nProcessing category: {cat_name}")
            
            if self.config['settings'].get('dynamic_keywords'):
                base_query = category.get('base_query', cat_name)
                candidates = category.get('candidate_keywords', [])
                # Use Daum for frequency analysis too as it's more reliable
                pool = self.fetch_daum_news(base_query, limit=10)
                counts = {kw: 0 for kw in candidates}
                for news in pool:
                    text = news['title'].lower()
                    for kw in candidates:
                        if kw.lower() in text: counts[kw] += 1
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_3 = [kw for kw, count in sorted_counts[:3]]
                if sum(counts.values()) == 0: top_3 = candidates[:3]
                keywords_to_search = top_3
            else:
                keywords_to_search = category.get('keywords', [])

            top_keywords_map[cat_name] = keywords_to_search
            cat_news = []
            seen_links = set()

            for kw in keywords_to_search:
                raw_news = []
                # Mix sources: Get some from Daum, some from Naver/Google
                if self.config['settings'].get('dynamic_keywords') and kw == category.get('base_query', cat_name):
                    # Reuse pool if we already fetched it
                    daum_news = pool[:self.config['settings']['max_news_per_category']]
                else:
                    daum_news = self.fetch_daum_news(kw, limit=self.config['settings']['max_news_per_category'])
                naver_news = self.fetch_naver_news(kw, limit=self.config['settings']['max_news_per_category'])
                google_news = self.fetch_google_news(kw, limit=self.config['settings']['max_news_per_category'])
                
                # Combine and interleave for variety
                combined = []
                max_len = max(len(daum_news), len(naver_news), len(google_news))
                for i in range(max_len):
                    if i < len(daum_news): combined.append(daum_news[i])
                    if i < len(naver_news): combined.append(naver_news[i])
                    if i < len(google_news): combined.append(google_news[i])
                
                raw_news = combined

                import re
                seen_titles = set()
                print(f"  - Total mixed news found for '{kw}': {len(raw_news)}")
                for news in raw_news:
                    if self.config['settings']['deduplicate']:
                        clean_title = re.sub(r'[^가-힣a-zA-Z0-9]', '', news['title'])
                        
                        is_duplicate = news['link'] in seen_links
                        if not is_duplicate and len(clean_title) > 10:
                            for st in seen_titles:
                                if clean_title in st or st in clean_title:
                                    is_duplicate = True
                                    break
                                    
                        if not is_duplicate:
                            news['keyword'] = kw
                            # Ensure date is clean
                            news['date'] = self._normalize_date(news.get('date'))
                            cat_news.append(news)
                            seen_links.add(news['link'])
                            seen_titles.add(clean_title)
                    else:
                        news['keyword'] = kw
                        news['date'] = self._normalize_date(news.get('date'))
                        cat_news.append(news)
            
            all_results[cat_name] = cat_news[:self.config['settings']['max_news_per_category'] * 2]
            print(f"  - Final list for '{cat_name}': {len(all_results[cat_name])} items")
            
        return all_results, top_keywords_map
            
        return all_results, top_keywords_map

if __name__ == "__main__":
    crawler = NewsCrawler()
    results = crawler.get_all_news()
    for cat, news in results.items():
        print(f"[{cat}] Found {len(news)} articles")
