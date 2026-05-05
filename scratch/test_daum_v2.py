import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://search.daum.net/',
}

url = f"https://search.daum.net/search?w=news&q={quote('DB손해보험')}"
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')

items = soup.select('.c-list-basic li')
for i, item in enumerate(items[:3]):
    title_elem = item.select_one('.item-tit a')
    title = title_elem.get_text(strip=True) if title_elem else "None"
    link = title_elem.get('href') if title_elem else "None"
    print(f"[{i}] Title: {title}")
    print(f"    Link: {link}")
    img = item.select_one('img')
    print(f"    Img: {img.get('data-original-src') or img.get('src') if img else 'None'}")
