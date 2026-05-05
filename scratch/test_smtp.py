import smtplib
import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)['email']

print(f"Testing SMTP with: {config['sender_email']}")
try:
    server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
    server.set_debuglevel(1) # Show detailed logs
    server.starttls()
    server.login(config['sender_email'], config['sender_password'])
    print("Login success!")
    server.quit()
except Exception as e:
    print(f"\nLogin failed: {e}")
