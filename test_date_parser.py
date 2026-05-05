from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def normalize_date(date_str):
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
            d = int(parts[2])
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
        except:
            pass
            
    return now.strftime('%m월%d일')

print(normalize_date('5시간 전'))
print(normalize_date('어제'))
print(normalize_date('2026.05.02'))
print(normalize_date('Sun, 03 May 2026 07:05:30 GMT'))
print(normalize_date(''))
