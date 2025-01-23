# email_otp.py
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def generate_otp(length=6):
    """Generate a numeric OTP code."""
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))


def send_otp_via_email(to_email, otp_code):
    """
    Sends the OTP code via Email. 
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "Your OTP Code"

        body = f"Your OTP code is: {otp_code}\nIt will expire soon."
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT)) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

