import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

#  Mailtrap SMTP Settings
SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525

#  Mailtrap Credentials (jo tum ne diye)
EMAIL_ADDRESS = "048ac875395b7f"
EMAIL_PASSWORD = "2efaf02675faff"


def send_email(to_email: str, subject: str, body: str) -> None:

    msg = MIMEMultipart()
    msg["From"] = "ShoppingwithBilal@example.com"  # sender can be anything in testing
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()  # TLS optional but recommended
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(msg["From"], to_email, msg.as_string())

        logger.info(" Email sent successfully")

    except Exception as e:
        logger.error(f" Email failed: {str(e)}")
