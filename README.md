# 📰 Daily News Aggregator & Email Newsletter System

이 프로젝트는 지정된 관심 키워드(예: 기업명, 신기술, 업계 동향 등)를 바탕으로 매일 아침 구글(Google), 네이버(Naver), 다음(Daum) 등 주요 포털에서 최신 뉴스를 자동으로 수집하고, 세련된 양식의 HTML 이메일 뉴스레터로 요약하여 발송해 주는 자동화 파이썬 스크립트입니다.

## ✨ 주요 기능
- 🔍 **다중 검색 엔진 지원**: 구글, 네이버, 다음 검색 엔진의 결과 혼합 수집
- ⏱️ **최신성 보장**: 이메일 발송 시점 기준 **최근 24시간 이내**에 보도된 기사만 필터링
- 🤖 **스마트 중복 제거**: 서로 다른 언론사/포털에서 발생한 동일한 기사(제목 부분 일치 등)를 알고리즘으로 판별하여 중복 제거
- 🏢 **실제 언론사 추출**: 단순 "네이버 뉴스"가 아닌 기사의 메타데이터(`og:site_name`)를 추적하여 실제 언론사명 기재
- 🎨 **엔터프라이즈 리포트 디자인**: 모바일과 PC 모두에서 가독성이 뛰어난 세련된 대시보드 UI 스타일의 이메일 발송
- ⏰ **스케줄링**: 스크립트를 켜두면 매일 지정된 시간(예: 오전 8시)에 자동으로 발송

## 🛠️ 설치 방법

1. **저장소 클론(Clone)**
   ```bash
   git clone https://github.com/21ckorea/DailyNews.git
   cd DailyNews
   ```

2. **파이썬 라이브러리 설치**
   의존성 패키지를 설치합니다. Python 3.8 이상을 권장합니다.
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ 설정 가이드

1. **환경 설정 파일 생성**
   보안을 위해 기본 제공되는 템플릿 파일을 복사하여 실제 설정 파일(`config.yaml`)을 생성합니다.
   ```bash
   cp config.yaml.dev config.yaml
   ```

2. **메일 발송 계정 설정 (`config.yaml`)**
   생성된 `config.yaml` 파일을 열고, 사용할 이메일 계정(Gmail 권장)과 앱 비밀번호를 설정합니다.
   ```yaml
   email:
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "발신자이메일@gmail.com"
     sender_password: "구글 앱 비밀번호 16자리" # (일반 비밀번호 아님)
     receiver_email: "수신자이메일@domain.com"
   ```
   > 💡 **앱 비밀번호 발급 방법 (Google)**
   > 1. 구글 계정 관리 > 보안 탭으로 이동
   > 2. **2단계 인증** 활성화
   > 3. 하단의 **앱 비밀번호** 생성 (앱 이름은 'DailyNews' 등으로 임의 설정)
   > 4. 화면에 나타난 16자리 비밀번호를 띄어쓰기 없이 복사하여 `sender_password`에 붙여넣기

3. **키워드 및 카테고리 설정 (선택 사항)**
   `config.yaml` 상단의 `categories` 항목을 수정하여 원하는 주제와 검색 키워드를 자유롭게 커스터마이징할 수 있습니다.

## 🚀 실행 방법

### 1. 스케줄러를 통한 자동 반복 실행 (백그라운드 구동)
아래 명령어를 통해 스크립트를 실행하면 설정된 시간에 맞춰 매일 반복 실행됩니다.
```bash
python3 main.py
```
* 실행 즉시 테스트 메일이 1회 발송되며, 스크립트를 켜두면 `config.yaml`에 설정된 `schedule_time` (예: "08:00")에 매일 자동으로 뉴스레터를 발송합니다.

### 2. 크론탭(Crontab)을 이용한 1회성 실행
만약 스크립트를 백그라운드에 계속 띄워두지 않고 서버의 `crontab` 등 외부 스케줄러를 사용하여 특정 시점에 한 번만 실행하고 종료되게 하려면 `--run-once` 옵션을 사용하세요.
```bash
python3 main.py --run-once
```
* **크론탭 설정 예시 (매일 아침 8시에 실행):**
  ```bash
  0 8 * * * cd /Users/ryan/work/python/DailyNews && /usr/bin/python3 main.py --run-once
  ```

## 📂 파일 구조
- `main.py`: 프로그램 진입점 및 스케줄러 실행
- `crawler.py`: 포털 검색 크롤링 및 중복/24시간 필터링 로직 핵심부
- `mailer.py`: SMTP 통신 및 이메일 발송 담당
- `templates/news_template.html`: 이메일 본문을 위한 커스텀 HTML/CSS 템플릿
- `config.yaml`: (사용자 생성) 인증 정보 및 검색 키워드 설정 파일
- `config.yaml.dev`: 초기 설정을 위한 템플릿 파일

---
**License**
MIT License
