import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

url = f"https://search.daum.net/search?w=news&q={quote('DB손해보험')}"
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')
items = soup.select('li')
print(f"Found {len(items)} items")
for item in items:
    title = item.select_one('.tit_main, .tit-main, a.link_txt')
    if title and 'DB손해보험' in title.get_text():
        print(f"Title: {title.get_text(strip=True)}")
        img = item.select_one('img')
        print(f"Img: {img.get('src') if img else 'None'}")
        break
else:
    print("No relevant Daum items found")
