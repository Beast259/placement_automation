# Placement Automation System - Quick Start Guide

## Files Created
```
placement_automation/
├── scraper.py              # Web scraping module
├── email_sender.py         # Email sending functionality
├── follow_up_manager.py    # Follow-up email tracking
├── main.py                 # Main orchestrator with scheduler
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template (copy to .env)
└── README.md               # Detailed instructions
```

## Immediate Next Steps (Manual)

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** with your credentials:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=your_app_password_here  # NOT your regular password!
   EMAIL_SUBJECT_PREFIX=[Placement Opportunity]
   HEAD_EMAIL=head_of_placement@yenepoya.edu.in
   ```

3. **Set up virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Test the system:**
   ```bash
   # Edit main.py to uncomment the test section:
   # automation = PlacementAutomation()
   # automation.run_daily_automation()
   python main.py
   ```

5. **For scheduled execution:**
   ```bash
   # Edit main.py to uncomment the scheduler section:
   # run_scheduler()
   python main.py  # Will run daily at 9:00 AM
   ```

## What the System Does Daily

- Sends up to 100 initial placement emails to companies
- Processes follow-up emails (every 3 days, max 2 per company)
- Generates daily report emailed to placement cell head
- Logs all activities to placement_automation.log
- Stores data in CSV files for tracking

## Customization

- Email templates: Edit in main.py (send_initial_emails & process_follow_ups)
- Target companies: Modify urls.txt or _create_sample_urls_file()
- Schedule time: Change in run_scheduler() function
- Follow-up intervals: Adjust in get_follow_ups_due() method

## Important Notes

⚠️ **For Gmail:** You MUST use an App Password, not your regular password
   - Enable 2-Factor Authentication first
   - Generate App Password in Google Account settings

⚠️ **Rate limiting:** The system sends emails in batches to avoid spam flags

⚠️ **Testing:** Start with a small number of emails to verify setup

## Verification Status

Code logic verified through mocking - all modules import and instantiate correctly.
Actual email sending and web scraping require proper credentials and network access.

---

**Ready for use once .env is configured and dependencies installed.**