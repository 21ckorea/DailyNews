import base64

url = 'https://news.google.com/rss/articles/CBMiRGh0dHBzOi8vdi5kYXVtLm5ldC92LzIwMjYwNDI5MjEwOTAwNTEx0gEA?oc=5'
encoded_part = url.split('articles/')[1].split('?')[0]
padding = '=' * (4 - len(encoded_part) % 4)
decoded_bytes = base64.b64decode(encoded_part + padding, validate=False)
decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
print(f"Decoded string: {decoded_str}")
if 'http' in decoded_str:
    final_url = 'http' + decoded_str.split('http')[1].split('\x00')[0].split('\x01')[0].split('\x02')[0]
    print(f"Final URL: {final_url}")
