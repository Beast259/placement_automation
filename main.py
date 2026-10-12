import csv
import os
from datetime import datetime, timedelta
from scraper import scrape_company_list, save_to_csv
from email_sender import EmailSender
from follow_up_manager import FollowUpManager
import schedule
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('placement_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlacementAutomation:
    def __init__(self):
        self.email_sender = EmailSender()
        self.follow_up_manager = FollowUpManager()
        self.daily_report_file = 'daily_report.csv'
        self.companies_file = 'companies.csv'
        self._initialize_daily_report()
    
    def _initialize_daily_report(self):
        """Initialize daily report file if it doesn't exist."""
        if not os.path.isfile(self.daily_report_file):
            with open(self.daily_report_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'emails_sent', 'follow_ups_sent', 'responses_received', 'new_companies_found'])
    
    def scrape_and_save_companies(self, urls_file='urls.txt'):
        """Scrape company emails and save to CSV."""
        logger.info("Starting company scraping...")
        try:
            # Create urls.txt if it doesn't exist with some example URLs
            if not os.path.isfile(urls_file):
                self._create_sample_urls_file(urls_file)
            
            data = scrape_company_list(urls_file)
            if data:
                save_to_csv(data, self.companies_file)
                logger.info(f"Scraped and saved {len(data)} company email records.")
                return len(data)
            else:
                logger.warning("No company data scraped.")
                return 0
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return 0
    
    def _create_sample_urls_file(self, filename):
        """Create a sample URLs file with some Indian company career pages."""
        sample_urls = [
            "https://www.tcs.com/careers",
            "https://www.infosys.com/careers/",
            "https://www.wipro.com/careers/",
            "https://www.hcltech.com/careers",
            "https://www.techmahindra.com/careers/",
            "https://www.lntinfotech.com/careers",
            "https://www.mindtree.com/careers",
            "https://www.coforge.com/careers",
            "https://www.persistent.com/careers/",
            "https://www.ltimindtree.com/careers"
        ]
        with open(filename, 'w') as f:
            for url in sample_urls:
                f.write(url + '\n')
        logger.info(f"Created sample URLs file: {filename}")
    
    def send_initial_emails(self, limit=100):
        """Send initial placement emails to companies."""
        logger.info(f"Sending initial emails (limit: {limit})...")
        
        # Read companies from CSV
        companies = []
        try:
            with open(self.companies_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    companies.append(row)
        except FileNotFoundError:
            logger.error(f"Companies file {self.companies_file} not found. Run scraping first.")
            return 0
        
        # Limit to requested number
        companies_to_email = companies[:limit]
        
        # Email body template
        email_body = """
Dear {name},

I hope this email finds you well. I am reaching out from Yenepoya deemed to be University, Bangalore, regarding potential placement opportunities for our talented students.

Our university has a strong pool of graduates across various disciplines including Engineering, Management, Pharmacy, and Allied Health Sciences. We believe our students would be valuable assets to your organization.

We would be delighted to discuss:
1. Campus placement drives at our Bangalore campus
2. Internship opportunities for our pre-final year students
3. Industry-academia collaboration initiatives
4. Skill development programs tailored to your needs

Please let us know a convenient time for a brief call or meeting to explore how we can collaborate for mutual benefit.

Thank you for your time and consideration.

Best regards,
Placement Cell
Yenepoya deemed to be University, Bangalore
placement@yenepoya.edu.in
+91-80-XXXXXXXX

Note: This is a confidential communication intended solely for the addressee. If you are not the intended recipient, please notify the sender immediately and delete this message.
"""
        
        # Prepare recipients
        recipients = []
        for company in companies_to_email:
            recipients.append({
                'email': company['email'],
                'name': company['company_name'] or 'Hiring Team',
                'company': company['company_name']
            })
        
        # Send emails
        sent_count = self.email_sender.send_bulk_emails(
            recipients, 
            email_body, 
            is_html=False
        )
        
        # Record sent emails and add to follow-up tracking
        for company in companies_to_email:
            if company['email'] in [r['email'] for r in recipients[:sent_count]]:
                self.follow_up_manager.add_follow_up(
                    company['email'], 
                    company['company_name'] or 'Unknown Company'
                )
                self.email_sender.record_sent_email(
                    company['email'],
                    company['company_name'] or 'Unknown Company',
                    'initial',
                    f"[Placement Opportunity] {company['company_name'] or 'Hiring Team'}"
                )
        
        logger.info(f"Sent {sent_count} initial emails.")
        return sent_count
    
    def process_follow_ups(self):
        """Process due follow-up emails."""
        logger.info("Processing follow-up emails...")
        
        due_follow_ups = self.follow_up_manager.get_follow_ups_due(days_interval=3, max_follow_ups=2)
        logger.info(f"Found {len(due_follow_ups)} follow-ups due.")
        
        if not due_follow_ups:
            return 0
        
        # Follow-up email templates
        follow_up_templates = [
            """Dear {name},

I hope you received my previous email regarding placement opportunities from Yenepoya deemed to be University, Bangalore. I wanted to follow up to see if you had any questions or if you'd like to discuss potential collaboration.

Our students are ready to contribute to organizations like yours, and we would be happy to arrange a virtual meeting at your convenience.

Best regards,
Placement Cell
Yenepoya deemed to be University, Bangalore""",
            
            """Dear {name},

This is my second follow-up regarding placement collaboration with Yenepoya deemed to be University, Bangalore. We have several upcoming placement drives and would be honored to include your esteemed organization.

If you're interested in participating, please let us know your preferred dates and we'll make the necessary arrangements.

Looking forward to hearing from you.

Best regards,
Placement Cell
Yenepoya deemed to be University, Bangalore"""
        ]
        
        sent_count = 0
        for follow_up in due_follow_ups:
            # Choose template based on follow-up count
            template_index = min(follow_up['follow_up_count'] - 1, len(follow_up_templates) - 1)
            body = follow_up_templates[template_index].replace('{name}', follow_up['company_name'] or 'Hiring Team')
            
            if self.email_sender.send_email(
                follow_up['recipient_email'],
                follow_up['company_name'] or 'Hiring Team',
                body
            ):
                sent_count += 1
                # Record the follow-up email
                self.email_sender.record_sent_email(
                    follow_up['recipient_email'],
                    follow_up['company_name'] or 'Unknown Company',
                    f'follow_up_{follow_up["follow_up_count"]}',
                    f"[Placement Opportunity] {follow_up['company_name'] or 'Hiring Team'}"
                )
                # Update follow-up record
                self.follow_up_manager.update_follow_up_after_send(follow_up['recipient_email'])
        
        logger.info(f"Sent {sent_count} follow-up emails.")
        return sent_count
    
    def check_for_responses(self):
        """Check for responses (this would typically involve email parsing).
        For now, we'll simulate by checking a responses file or leave as placeholder."""
        logger.info("Checking for responses...")
        # In a real implementation, this would connect to email server and check for replies
        # For now, we'll return 0 as we don't have email parsing set up
        return 0
    
    def generate_daily_report(self, emails_sent, follow_ups_sent, responses_received, new_companies):
        """Generate and save daily report."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        with open(self.daily_report_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([today, emails_sent, follow_ups_sent, responses_received, new_companies])
        
        logger.info(f"Daily report saved for {today}")
        
        # Also send email report to head (configured via environment variables)
        self._send_report_to_head(emails_sent, follow_ups_sent, responses_received, new_companies)
    
    def _send_report_to_head(self, emails_sent, follow_ups_sent, responses_received, new_companies):
        """Send daily report email to the head of placement cell."""
        head_email = os.getenv('HEAD_EMAIL')
        if not head_email:
            logger.warning("HEAD_EMAIL not configured. Skipping report email to head.")
            return
        
        subject = f"Daily Placement Automation Report - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""
Daily Placement Automation Report
Date: {datetime.now().strftime('%Y-%m-%d')}

Summary:
- Initial placement emails sent: {emails_sent}
- Follow-up emails sent: {follow_ups_sent}
- Responses received: {responses_received}
- New companies found today: {new_companies}

This is an automated report from the Yenepoya University Placement Automation System.
"""
        
        self.email_sender.send_email(
            head_email,
            "Head of Placement Cell",
            body
        )
        logger.info(f"Report email sent to head: {head_email}")
    
    def run_daily_automation(self):
        """Run the complete daily automation cycle."""
        logger.info("Starting daily placement automation cycle...")
        
        # Step 1: Scrape for new companies (optional - can be done less frequently)
        # new_companies = self.scrape_and_save_companies()
        # For daily run, we might skip scraping to avoid being too aggressive
        new_companies = 0  # Placeholder
        
        # Step 2: Send initial emails (up to 100 per day)
        emails_sent = self.send_initial_emails(limit=100)
        
        # Step 3: Process follow-ups
        follow_ups_sent = self.process_follow_ups()
        
        # Step 4: Check for responses
        responses_received = self.check_for_responses()
        
        # Step 5: Generate daily report
        self.generate_daily_report(emails_sent, follow_ups_sent, responses_received, new_companies)
        
        logger.info("Daily placement automation cycle completed.")
        return {
            'emails_sent': emails_sent,
            'follow_ups_sent': follow_ups_sent,
            'responses_received': responses_received,
            'new_companies_found': new_companies
        }

def run_scheduler():
    """Run the automation on a schedule."""
    automation = PlacementAutomation()
    
    # Schedule daily run at 9:00 AM
    schedule.every().day.at("09:00").do(automation.run_daily_automation)
    
    # Also run once immediately for testing
    # automation.run_daily_automation()
    
    logger.info("Scheduler started. Waiting for scheduled tasks...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Uncomment one of the following based on how you want to run:
    
    # Option 1: Run once immediately (good for testing)
    # automation = PlacementAutomation()
    # automation.run_daily_automation()
    
    # Option 2: Run on schedule (uncomment the scheduler function and comment above)
    # run_scheduler()
    
    # Option 3: Just scrape companies (first step)
    # automation = PlacementAutomation()
    # automation.scrape_and_save_companies()
    
    print("Placement Automation System")
    print("===========================")
    print("To run:")
    print("1. Edit .env file with your email credentials")
    print("2. Uncomment the desired execution method in __main__")
    print("3. Run: python main.py")