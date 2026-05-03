# Daily News Email System Implementation Plan v0.1

This system will crawl news articles based on user-defined keywords and send a premium-styled HTML email every morning at 8:00 AM, replicating the "DB Daily News" layout provided in the image.

## User Review Required

> [!IMPORTANT]
> **Email Credentials**: You will need to provide SMTP settings (e.g., Gmail App Password) to send emails.
> **News Source**: The system will primarily use Naver News for high-quality Korean news results.
> **Server Environment**: To run this at 8 AM every day, the script needs to be hosted on a machine that is always on (e.g., a local server, AWS EC2, or a Raspberry Pi). Alternatively, we can use GitHub Actions for scheduling if the repository is private.

## Proposed Changes

The system will be structured into several modules for better maintainability.

### 1. Configuration Module
- **[NEW] config.yaml**: Stores keywords, categories, and email settings.

### 2. News Crawler Module
- **[NEW] crawler.py**: Uses `requests` and `BeautifulSoup` to fetch news data from Naver. It will extract:
    - Title and Link
    - Publisher (News source)
    - Relative date (e.g., "05월 03일")
    - Thumbnail image URL
    - Keywords/Hashtags

### 3. Email Template Module
- **[NEW] templates/news_template.html**: A Jinja2-based HTML template designed to match the "DB Daily News" aesthetic.
    - Responsive 3-column layout.
    - Premium styling: Google Fonts (Inter/Outfit), smooth gradients, and card-based design.

### 4. Mailer Module
- **[NEW] mailer.py**: Handles SMTP connection and sends the HTML content.

### 5. Main Execution & Scheduler
- **[NEW] main.py**: The entry point that integrates all modules and uses `apscheduler` to run at 8 AM daily.

## Verification Plan

### Automated Tests
- Test crawler with sample keywords to ensure data extraction works.
- Send a test email to verify layout and image rendering across different email clients (Gmail, Outlook).

### Manual Verification
- Verify that the 8 AM schedule triggers correctly.
- Check the visual fidelity of the email against the requested design.
