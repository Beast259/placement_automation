# Placement Automation System - Setup Instructions

## Overview
This system automates the process of:
1. Scraping email addresses from Indian company websites
2. Sending initial placement emails to companies
3. Managing follow-up emails for non-responders
4. Tracking responses and generating daily reports

## Setup Instructions

### 1. Environment Configuration
- Copy `.env.example` to `.env`: `cp .env.example .env`
- Edit `.env` file with your actual credentials:
  ```
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SENDER_EMAIL=your_email@gmail.com
  SENDER_PASSWORD=your_app_password  # Use app password for Gmail
  EMAIL_SUBJECT_PREFIX=[Placement Opportunity]
  HEAD_EMAIL=head_of_placement@yenepoya.edu.in
  ```

### 2. Install Dependencies
Since the system Python is externally managed, use one of these options:

**Option A: Use virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option B: Install with pip using --break-system-packages** (not recommended)
```bash
pip install --break-system-packages -r requirements.txt
```

**Option C: Use pipx** (if available)
```bash
pipx install -r requirements.txt
```

### 3. Prepare URLs
The system will automatically create a `urls.txt` file with sample Indian IT company career pages if it doesn't exist.
To use your own list, create a `urls.txt` file with one company URL per line.

### 4. Run the Automation

**For immediate execution (testing):**
```bash
python main.py
```
Uncomment the appropriate section in `main.py` under `if __name__ == "__main__":`

**For scheduled execution:**
```bash
python main.py
```
Uncomment the scheduler section in `main.py` under `if __name__ == "__main__":`
The system will run daily at 9:00 AM.

### 5. How It Works

**Daily Process:**
1. Sends initial placement emails to up to 100 companies from the database
2. Processes any follow-up emails that are due (sent every 3 days, max 2 follow-ups)
3. Checks for responses (requires email parsing setup - currently returns 0)
4. Generates a daily report and emails it to the placement cell head

**File Storage:**
- `companies.csv`: Stores scraped company email data
- `follow_ups.csv`: Tracks follow-up email schedule
- `sent_emails.csv`: Records all sent emails for tracking
- `daily_report.csv`: Logs daily statistics
- `placement_automation.log`: Detailed activity log

## Customization

### Email Templates
Edit the email body templates in `main.py`:
- Initial email: In `send_initial_emails()` method
- Follow-up emails: In `process_follow_ups()` method (two templates)

### Scraping Targets
Modify the sample URLs in `_create_sample_urls_file()` method in `main.py`
Or provide your own `urls.txt` file

### Schedule Timing
Change the schedule time in `run_scheduler()` function in `main.py`:
```python
schedule.every().day.at("09:00").do(automation.run_daily_automation")
```

## Notes
- For Gmail, you must use an App Password, not your regular password
- Enable 2-Factor Authentication on your Google account to generate App Passwords
- The system respects rate limits by sending emails in batches
- All email sending is logged for auditing
- No emails are sent during verification/testing without explicit credential configuration

## Troubleshooting
- Check `placement_automation.log` for detailed error information
- Verify SMTP connection by testing with a single email first
- Ensure outgoing port 587 is not blocked by your network/firewall
- For initial testing, consider reducing the email limit in `send_initial_emails()`

## Support
For issues or enhancements, please refer to the code comments or contact the system administrator.