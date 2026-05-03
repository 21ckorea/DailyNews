# Daily News Email System Implementation Plan v0.4

This version adds **Dynamic Keyword Selection** based on news frequency analysis, as shown in the provided "Data Analysis" images.

## Proposed Changes

### 1. Configuration Module
- **[MODIFY] config.yaml**: 
    - Each category now has a `base_query` (e.g., "DB그룹") and a list of `candidate_keywords` (entities to track).
    - Added `dynamic_keywords: true` setting.

### 2. Multi-source News Crawler Module
- **[MODIFY] crawler.py**: 
    - **Frequency Analysis**: For each category, the crawler first fetches a large pool of news using the `base_query`.
    - **Top 3 Selection**: It counts the occurrences of `candidate_keywords` in the titles and snippets of the pooled news.
    - **Dynamic Filtering**: The Top 3 most mentioned keywords are selected for the daily report.
    - **Categorized Results**: News items are grouped under these Top 3 keywords.

### 3. Email Template Module
- **[MODIFY] templates/news_template.html**:
    - Updated to reflect that keywords are dynamically chosen.
    - (Optional) Added a small visual indicator for "Mention Frequency".

### 4. Main Execution & Scheduler
- **[MODIFY] main.py**: Updated to handle the dynamic keyword mapping.

## Verification Plan

### Automated Tests
- Verify that the frequency counter correctly identifies the Top 3 keywords from a sample news pool.
- Ensure the email correctly displays the selected Top 3.

### Manual Verification
- Compare the selected Top 3 with manual search results to ensure accuracy.
