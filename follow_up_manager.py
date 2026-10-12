import csv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class FollowUpManager:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.subject_prefix = os.getenv('EMAIL_SUBJECT_PREFIX', '[Placement Opportunity]')
        self.follow_up_file = 'follow_ups.csv'
        self.sent_emails_file = 'sent_emails.csv'
        self._initialize_files()

    def _initialize_files(self):
        """Initialize CSV files if they don't exist."""
        # Follow-ups file
        if not os.path.isfile(self.follow_up_file):
            with open(self.follow_up_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['recipient_email', 'company_name', 'original_email_date', 'follow_up_count', 'last_follow_up_date', 'status'])
        
        # Sent emails file (for tracking)
        if not os.path.isfile(self.sent_emails_file):
            with open(self.sent_emails_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['recipient_email', 'company_name', 'email_type', 'sent_date', 'subject', 'response_received'])

    def add_follow_up(self, recipient_email, company_name, original_email_date=None):
        """Add a recipient to follow-up tracking."""
        if original_email_date is None:
            original_email_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if already exists
        if not self._exists_in_follow_ups(recipient_email):
            with open(self.follow_up_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([recipient_email, company_name, original_email_date, 0, original_email_date, 'pending'])
    
    def _exists_in_follow_ups(self, recipient_email):
        """Check if email already exists in follow-ups."""
        try:
            with open(self.follow_up_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if row and row[0] == recipient_email:
                        return True
        except FileNotFoundError:
            pass
        return False

    def record_sent_email(self, recipient_email, company_name, email_type, subject):
        """Record that an email was sent."""
        with open(self.sent_emails_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([recipient_email, company_name, email_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subject, ''])

    def record_response(self, recipient_email):
        """Mark that a response was received from a recipient."""
        # Update sent_emails file
        rows = []
        try:
            with open(self.sent_emails_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                rows.append(header)
                for row in reader:
                    if row and row[0] == recipient_email:
                        row[5] = 'yes'  # Mark response received
                    rows.append(row)
        except FileNotFoundError:
            # If file doesn't exist, create with header
            rows = [['recipient_email', 'company_name', 'email_type', 'sent_date', 'subject', 'response_received']]
        
        with open(self.sent_emails_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        # Update follow-ups: remove or mark as completed
        self._update_follow_up_status(recipient_email, 'completed')

    def _update_follow_up_status(self, recipient_email, status):
        """Update the status of a follow-up."""
        rows = []
        try:
            with open(self.follow_up_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                rows.append(header)
                for row in reader:
                    if row and row[0] == recipient_email:
                        row[5] = status  # Update status column
                    rows.append(row)
        except FileNotFoundError:
            rows = [['recipient_email', 'company_name', 'original_email_date', 'follow_up_count', 'last_follow_up_date', 'status']]
        
        with open(self.follow_up_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def get_follow_ups_due(self, days_interval=3, max_follow_ups=2):
        """
        Get list of follow-ups that are due.
        days_interval: days between follow-ups
        max_follow_ups: maximum number of follow-ups to send
        """
        due_follow_ups = []
        try:
            with open(self.follow_up_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    if not row or len(row) < 6:
                        continue
                    
                    recipient_email, company_name, original_email_date, follow_up_count, last_follow_up_date, status = row
                    
                    # Skip if already completed or max follow-ups reached
                    if status == 'completed' or int(follow_up_count) >= max_follow_ups:
                        continue
                    
                    # Check if it's time for a follow-up
                    last_follow_up = datetime.strptime(last_follow_up_date, '%Y-%m-%d %H:%M:%S')
                    if datetime.now() - last_follow_up >= timedelta(days=days_interval):
                        due_follow_ups.append({
                            'recipient_email': recipient_email,
                            'company_name': company_name,
                            'follow_up_count': int(follow_up_count) + 1,
                            'original_email_date': original_email_date
                        })
        except FileNotFoundError:
            pass
        
        return due_follow_ups

    def update_follow_up_after_send(self, recipient_email):
        """Update follow-up record after sending a follow-up email."""
        rows = []
        try:
            with open(self.follow_up_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                rows.append(header)
                for row in reader:
                    if row and row[0] == recipient_email:
                        # Increment follow-up count and update last follow-up date
                        row[3] = str(int(row[3]) + 1)  # follow_up_count
                        row[4] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # last_follow_up_date
                    rows.append(row)
        except FileNotFoundError:
            pass
        
        with open(self.follow_up_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def send_email_via_smtp(self, recipient_email, recipient_name, body, is_html=False):
        """Send email using SMTP (same as in email_sender.py but simplified for this class)."""
        if not self.sender_email or not self.sender_password:
            print("Error: Sender email or password not configured.")
            return False

        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = recipient_email
        message["Subject"] = f"{self.subject_prefix} {recipient_name}" if recipient_name else self.subject_prefix

        if is_html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = message.as_string()
                server.sendmail(self.sender_email, recipient_email, text)
            print(f"Follow-up email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"Error sending follow-up email to {recipient_email}: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    manager = FollowUpManager()
    # Set environment variables or create a .env file with:
    # SMTP_SERVER=smtp.gmail.com
    # SMTP_PORT=587
    # SENDER_EMAIL=your_email@gmail.com
    # SENDER_PASSWORD=your_a...rd
    # EMAIL_SUBJECT_PREFIX=[Placement Opportunity]
    
    # Add a follow-up (normally done after sending initial email)
    # manager.add_follow_up("company@example.com", "Example Company")
    
    # Check for due follow-ups
    # due = manager.get_follow_ups_due()
    # print(f"Due follow-ups: {len(due)}")
    # for follow_up in due:
    #     print(f"  - {follow_up['recipient_email']} (follow-up #{follow_up['follow_up_count']})")