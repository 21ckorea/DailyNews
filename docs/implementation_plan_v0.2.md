# Daily News Email System Implementation Plan v0.2

This system will crawl news articles based on user-defined keywords from multiple sources and send a premium-styled HTML email every morning at 8:00 AM, replicating the "DB Daily News" layout provided in the image.

## User Review Required

> [!IMPORTANT]
> **Email Credentials**: You will need to provide SMTP settings (e.g., Gmail App Password) to send emails.
> **News Source**: The system now uses **Multi-source Integration** (Naver News + Google News) to ensure the widest possible coverage, including all major and niche Korean news outlets.
> **Server Environment**: To run this at 8 AM every day, the script needs to be hosted on a machine that is always on.

## Proposed Changes

### 1. Configuration Module
- **[MODIFY] config.yaml**: Added source selection and deduplication settings.

### 2. Multi-source News Crawler Module
- **[NEW] crawler.py**: 
    - **Naver News Integration**: Primary source for high-quality Korean news with thumbnails and specific publisher info (NewsWay, Yonhap, etc.).
    - **Google News Integration**: Secondary source for broader coverage including niche blogs and international perspectives.
    - **Deduplication Logic**: Ensures the same article from different sources isn't sent twice.
    - **Data Extraction**: Title, Link, Publisher, Date, Thumbnail URL, Snippet.

### 3. Email Template Module
- **[MODIFY] templates/news_template.html**:
    - Enhanced layout to handle multi-source data.
    - Premium styling: Google Fonts, card-based design with "Source" badges.

### 4. Mailer Module
- **[NEW] mailer.py**: Handles SMTP connection and sends the HTML content.

### 5. Main Execution & Scheduler
- **[NEW] main.py**: The entry point that integrates all modules and uses `apscheduler` to run at 8 AM daily.

## Verification Plan

### Automated Tests
- Test crawler with sample keywords to ensure data from both Naver and Google are merged correctly.
- Verify deduplication logic works as expected.

### Manual Verification
- Check the visual fidelity of the email.
- Ensure the 8 AM trigger works consistently.
