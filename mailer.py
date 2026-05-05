import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml

class Mailer:
    def __init__(self, config):
        self.config = config['email']

    def send_email(self, subject, html_content, recipients=None):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.config['sender_email']
        
        # Use provided recipients or fallback to config
        target_recipients = recipients or self.config.get('receiver_email', [])
        
        if isinstance(target_recipients, list):
            receiver_str = ", ".join(target_recipients)
        else:
            receiver_str = str(target_recipients)
            
        msg['To'] = receiver_str

        part = MIMEText(html_content, 'html')
        msg.attach(part)

        try:
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            print(f"Email sent successfully to {receiver_str}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
