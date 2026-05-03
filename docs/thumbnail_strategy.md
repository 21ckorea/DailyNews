# 썸네일 이미지 추출 전략 (crawler.py)

> 작성일: 2026-05-03  
> 관련 파일: `crawler.py` → `extract_og_image(url, title="")`

---

## 1. 전체 흐름 개요

```
Google News URL 여부 판별
        │
        ├── [구글 뉴스] ──▶ STEP 1: 이진 해독 (Base64 Protobuf)
        │                         │ 성공 → 실제 기사 URL 확보
        │                         │ 실패 ↓
        │                   STEP 2: 제목 기반 역추적 (Daum → Naver)
        │                         │ 성공 → 실제 기사 URL 확보
        │                         │ 실패 → None 반환 (이미지 없음)
        │
        └── [기타 URL] ──▶ STEP 3: 이미지 직접 추출
                                   twitter:image → og:image → nate:image → 본문 첫 이미지
```

---

## 2. STEP 1 — 이진 해독 (Google News Protobuf Decode)

- **대상**: `news.google.com/rss/articles/CBM...` 형태의 RSS 암호화 URL
- **방법**: URL의 `articles/` 뒤 부분을 Base64 디코딩하여, 내부에 포함된 `https://` 실제 기사 주소를 정규식으로 추출
- **성공 조건**: 디코딩 결과에서 `google.com`, `gstatic.com`, `angular.dev`가 아닌 URL 발견 시
- **실패 사례**: 구글이 암호화 방식을 강화하거나 신규 인코딩 포맷 사용 시

```python
encoded_part = url.split('articles/')[1].split('?')[0]
raw_data = base64.urlsafe_b64decode(encoded_part + padding)
url_matches = re.findall(rb'https?://...', raw_data)
```

---

## 3. STEP 2 — 제목 기반 역추적 (Title Reverse Search)

이진 해독 실패 시, `title` 파라미터를 활용해 포털 뉴스 검색으로 원본 기사 URL을 역추적합니다.

### 제목 정제 규칙
1. ` - 언론사명`, ` | 언론사명` 제거
2. `[]` 대괄호 제거 (예: `[DB그룹 동곡재단]` → `DB그룹 동곡재단`)
3. 제목에 `,`가 많을 경우 가장 긴 구절만 사용
4. 작은따옴표/큰따옴표 제거

### 검색 순서

| 순서 | 엔진 | URL 형식 | 셀렉터 |
|------|------|----------|--------|
| 1차 | **Daum 뉴스** | `search.daum.net/search?w=news&q="{제목}"` | `.item-title a` |
| 2차 | **Daum 뉴스** | 위와 동일, 제목 앞 25자만 사용 | `.item-title a` |
| 3차 | **Naver 뉴스** | `search.naver.com/search.naver?where=news&query=` | `a.news_tit` |

> **Note**: Naver는 봇 차단이 강해 성공률이 낮습니다. Daum이 1차 의존 엔진입니다.

### 역추적 성공 조건
- 반환된 링크가 `http`로 시작
- `google.com`, `naver.com/search` 등 검색 결과 페이지 URL이 아닐 것

---

## 4. STEP 3 — 이미지 직접 추출

실제 기사 URL에 접근하여 아래 순서로 이미지를 추출합니다.

### 4-1. 메타 태그 우선 탐색 (권장)

```
twitter:image  →  og:image  →  nate:image
```

- `property` 속성과 `name` 속성을 모두 확인
- `//`로 시작하는 주소는 `https:`를 자동 보완
- 광고 패턴 필터링 적용

### 4-2. 본문 이미지 폴백

메타 태그에서 유효한 이미지를 못 찾을 경우, 아래 CSS 셀렉터 순서로 기사 본문 컨테이너를 찾아 **첫 번째 이미지**를 사용합니다.

```
.view_body
#articleBody
#article-view-content-div
#articleBodyContents
article
.article_view
.view_content
.article-body
.news_cont
```

### 4-3. 광고 필터 (ad_patterns)

다음 패턴이 URL에 포함된 이미지는 자동으로 제외됩니다:

```python
['adv.', 'realmedia', 'banner', 'pixel', 'spacer', 'vending']
```

---

## 5. Daum 기사 처리 (`fetch_daum_news`)

Daum 뉴스 검색 결과 링크는 항상 `v.daum.net/v/...` 래핑 URL 형태입니다.  
이 URL로 요청 시 **Daum 뷰어 페이지**가 열리며, `og:image`에는 이미 Daum CDN으로 최적화된 이미지가 제공됩니다.

```
http://v.daum.net/v/{ID}
  → og:image: https://img1.daumcdn.net/thumb/S1200x630/?fname=https://t1.daumcdn.net/...
```

이 경우 `extract_og_image`를 통해 **안정적으로 썸네일이 추출**됩니다.  
Daum 이미지 추출 실패 시, 검색 결과 카드의 `img` 태그를 폴백으로 사용합니다.

---

## 6. ⚠️ 미해결 과제 — 이미지 추출 불가 언론사 3곳

아래 3개 언론사는 현재 자동 썸네일 추출이 불가합니다. **추후 별도 처리 필요**.

---

### 6-1. 글로벌이코노믹 (`g-enews.com`)

- **구글 뉴스 URL**: `CBMiiwFBVV95...` 형태
- **실제 기사 URL**: `https://www.g-enews.com/article/General-News/2026/04/202604300944084118daecd3dad5_1`
- **문제**: 이진 해독 실패 + Daum 역추적 시 **동일 제목의 2025년 기사**가 잘못 매칭됨
- **메타 태그 상태**:
  - `twitter:image` → `https://nimage.g-enews.com/phpwas/restmb_allidxmake.php?idx=5&simg=...` ✅ (유효)
  - `og:image` → 동일
- **원인**: 제목 키워드가 너무 일반적 (`드라이빙 레인지`)이어서 다른 연도 기사와 혼동
- **해결 방안 아이디어**:
  - 제목 + 날짜(발행일)를 조합한 검색 쿼리 사용
  - `site:g-enews.com` 검색 파라미터 활용

---

### 6-2. 뉴스로드 (`newsroad.co.kr`)

- **구글 뉴스 URL**: `CBMia0FVX3lx...` 형태
- **실제 기사 URL**: `https://www.newsroad.co.kr/news/articleView.html?idxno=58887`
- **문제**: Daum/Naver/Bing 뉴스 인덱스에 **미등록 언론사** → 역추적 완전 불가
- **메타 태그 상태** (직접 접근 시):
  - `twitter:image` → `https://cdn.newsroad.co.kr/news/thumbnail/202605/58887_79106_4313_v150.jpg` ✅
  - 본문 이미지 → `https://cdn.newsroad.co.kr/news/photo/202605/58887_79106_4313.jpg` ✅ (더 고화질)
- **원인**: 구글 뉴스 URL → 실제 기사 URL 변환 수단 없음
- **해결 방안 아이디어**:
  - Playwright/Selenium으로 구글 뉴스 링크 클릭 후 리다이렉트 URL 캡처
  - 구글 뉴스 웹페이지 HTML 파싱 (JavaScript 렌더링 필요)

---

### 6-3. 딜사이트 (`dealsite.co.kr`)

- **구글 뉴스 URL**: `CBMiT0FVX3lx...` 형태
- **실제 기사 URL**: `https://dealsite.co.kr/articles/127571`
- **문제**: Daum/Naver/Bing 뉴스 인덱스에 **미등록 언론사** → 역추적 완전 불가
- **메타 태그 상태** (직접 접근 시):
  - `twitter:image` → `https://dtd31o1ybbmk8.cloudfront.net/photos/.../thumb.jpg` (썸네일)
  - 본문 셀렉터 매칭 없음 → 이미지 추출 불가
- **원인**: 구글 뉴스 URL → 실제 기사 URL 변환 수단 없음 + 본문 셀렉터 미지원
- **해결 방안 아이디어**:
  - 뉴스로드와 동일 (Playwright)
  - 딜사이트 전용 본문 셀렉터 추가 (`main-article-content` 등 실제 확인 필요)

---

## 7. 공통 기술적 한계 및 개선 방향

| 한계 | 설명 | 개선 방향 |
|------|------|-----------|
| 구글 RSS URL 해독 실패 | 구글이 암호화 방식을 주기적으로 변경 | Playwright로 JS 리다이렉트 추적 |
| Naver 봇 차단 | 서버 사이드 요청에 대한 강력한 차단 | 모바일 UA + 세션 쿠키 + 딜레이 조합 |
| 소규모 언론사 미인덱스 | 뉴스로드, 딜사이트 등 포털 미등록 | 별도 화이트리스트 URL 패턴 관리 |
| 광고/썸네일 이미지 혼용 | 언론사별 메타 태그 품질 편차 큼 | 언론사별 맞춤 셀렉터 DB 구축 |
