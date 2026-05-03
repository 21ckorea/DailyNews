import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml

class Mailer:
    def __init__(self, config):
        self.config = config['email']

    def send_email(self, subject, html_content):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.config['sender_email']
        receiver = self.config['receiver_email']
        if isinstance(receiver, list):
            receiver_str = ", ".join(receiver)
        else:
            receiver_str = str(receiver)
            
        msg['To'] = receiver_str

        part = MIMEText(html_content, 'html')
        msg.attach(part)

        try:
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            print(f"Email sent successfully to {self.config['receiver_email']}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
