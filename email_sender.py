import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')  # Use app password for Gmail
        self.subject_prefix = os.getenv('EMAIL_SUBJECT_PREFIX', '[Placement Opportunity]')

    def send_email(self, recipient_email, recipient_name, body, is_html=False, attachment_path=None):
        """
        Send an email to a recipient.
        Returns True if successful, False otherwise.
        """
        if not self.sender_email or not self.sender_password:
            print("Error: Sender email or password not configured.")
            return False

        # Create message
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = recipient_email
        message["Subject"] = f"{self.subject_prefix} {recipient_name}" if recipient_name else self.subject_prefix

        # Add body
        if is_html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        # Add attachment if provided
        if attachment_path and os.path.isfile(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            message.attach(part)

        # Send email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = message.as_string()
                server.sendmail(self.sender_email, recipient_email, text)
            print(f"Email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"Error sending email to {recipient_email}: {e}")
            return False

    def send_bulk_emails(self, recipients, body_template, is_html=False, attachment_path=None):
        """
        Send emails to multiple recipients.
        recipients: list of dicts with keys 'email' and optionally 'name'
        Returns count of successfully sent emails.
        """
        sent_count = 0
        for recipient in recipients:
            email = recipient.get('email')
            name = recipient.get('name', '')
            if not email:
                continue
            # Personalize body (simple placeholder replacement)
            body = body_template.replace('{name}', name).replace('{company}', recipient.get('company', ''))
            if self.send_email(email, name, body, is_html, attachment_path):
                sent_count += 1
        return sent_count

if __name__ == "__main__":
    # Example usage
    sender = EmailSender()
    # Set environment variables or create a .env file with:
    # SMTP_SERVER=smtp.gmail.com
    # SMTP_PORT=587
    # SENDER_EMAIL=your_email@gmail.com
    # SENDER_PASSWORD=your_app_password
    # EMAIL_SUBJECT_PREFIX=[Placement Opportunity]

    # Test with a single email (uncomment to test)
    # result = sender.send_email(
    #     recipient_email="test@example.com",
    #     recipient_name="Test User",
    #     body="Hello {name},\n\nThis is a test email from the placement automation system.\n\nBest regards,\nPlacement Cell\nYenepoya deemed to be University",
    # )
    # print(f"Send result: {result}")