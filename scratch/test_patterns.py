import base64
import re

def test_decode(encoded_part):
    try:
        padding = '=' * (4 - len(encoded_part) % 4)
        decoded_bytes = base64.b64decode(encoded_part + padding, validate=False)
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        print(f"Decoded: {decoded_text}")
        match = re.search(r'https?://[^\s\x00-\x1f\x7f-\xff]+', decoded_text)
        if match:
            print(f"Found URL: {match.group(0)}")
        else:
            print("No URL found in decoded text")
    except Exception as e:
        print(f"Error: {e}")

print("--- Testing pattern 1 (CEO) ---")
test_decode("CBMiRGh0dHBzOi8vdi5kYXVtLm5ldC92LzIwMjYwNDI5MjEwOTAwNTEx0gEA")

print("\n--- Testing pattern 2 (From logs) ---")
test_decode("CBMiT0FVX3lxTFA0cVo2ZU9SWV82YjZvU3FOOGl5cVVvUXRUejNkM3phTDVHT19Ra25NWko3MDdmUjhicHQxMXpsRFpXdEp5M3BDQU1FTkNrSTQ")
