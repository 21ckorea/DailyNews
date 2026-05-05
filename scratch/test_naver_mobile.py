import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

url = f"https://m.search.naver.com/search.naver?where=m_news&query={quote('DB손해보험')}"
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')
items = soup.select('.news_wrap')
print(f"Found {len(items)} items")
if items:
    title = items[0].select_one('.news_tit')
    print(f"Title: {title.get_text(strip=True) if title else 'None'}")
    img = items[0].select_one('img')
    print(f"Img: {img.get('src') or img.get('data-src') if img else 'None'}")
