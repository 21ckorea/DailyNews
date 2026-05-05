# 📰 Daily News Aggregator & Email Newsletter System

이 프로젝트는 지정된 관심 키워드(예: 기업명, 신기술, 업계 동향 등)를 바탕으로 매일 아침 구글(Google), 네이버(Naver), 다음(Daum) 등 주요 포털에서 최신 뉴스를 자동으로 수집하고, 세련된 양식의 HTML 이메일 뉴스레터로 요약하여 발송해 주는 자동화 파이썬 스크립트입니다.

## ✨ 주요 기능
- 🔍 **다중 검색 엔진 지원**: 구글, 네이버, 다음 검색 엔진의 결과 혼합 수집
- ⏱️ **최신성 보장**: 이메일 발송 시점 기준 **최근 24시간 이내**에 보도된 기사만 필터링
- 🤖 **스마트 중복 제거 및 필터링**: 제목 기반 중복 제거는 물론, 사이드바 광고나 무관한 태그성 기사를 걸러내는 **2차 검증 로직** 탑재
- 👥 **멀티 그룹 발송**: 수신자별로 서로 다른 카테고리 조합을 구성하여 개인화된 뉴스레터 발송 가능 (동일 카테고리는 1회만 크롤링하여 최적화)
- 🏢 **실제 언론사 추출**: 기사의 메타데이터를 추적하여 실제 언론사명과 썸네일 이미지를 정확하게 추출
- 🎨 **엔터프라이즈 리포트 디자인**: 모바일과 PC 모두에서 가독성이 뛰어난 세련된 대시보드 UI 스타일의 이메일 발송

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

2. **이메일 및 수신 그룹 설정 (`config.yaml`)**
   ```yaml
   ai:
     trend_top_n: 100        # 동적 키워드 추출 시 최대 키워드 개수
     request_delay: 1.0     # 검색 엔진 요청 간 대기 시간(초)

   email:
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "발신자@gmail.com"
     sender_password: "앱비밀번호"

   mailing_groups:
     - name: "운영팀"
       recipients: ["user1@domain.com"]
       categories: ["보험개발원", "DT신기술"]
     - name: "기획팀"
       recipients: ["user2@domain.com", "user3@domain.com"]
       categories: ["IT업계동향", "DT신기술"]
   ```

3. **키워드 및 카테고리 설정**
   `categories` 항목에 각 그룹에서 사용할 카테고리 이름과 키워드를 정의합니다.

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

## 🔄 최신 버전으로 업데이트

서버나 로컬 환경에서 소스 코드를 최신 버전으로 유지하려면 다음 명령어를 실행하세요.

```bash
git pull origin main
```
* 업데이트 후 새로운 라이브러리가 추가되었을 수 있으므로 다시 한번 패키지를 설치해 주는 것이 좋습니다.
  ```bash
  pip install -r requirements.txt
  ```

## 📂 파일 구조
- `main.py`: 프로그램 진입점, 멀티 그룹 배분 및 스케줄러 실행
- `crawler.py`: 뉴스 수집, 랭킹 계산, 2차 검증(Relevance Filter) 및 중복 제거 핵심 로직
- `mailer.py`: SMTP 통신 및 멀티 수신자 발송 담당
- `keyword_extractor.py`: 검색량 기반 실시간 키워드 분석 및 추출
- `templates/news_template.html`: Jinja2 기반의 동적 HTML 뉴스레터 템플릿
- `config.yaml`: 사용자 맞춤 설정 (카테고리, 그룹, 수신자 등)
- `config.yaml.dev`: 초기 설정을 위한 템플릿 파일

---
**License**
MIT License
