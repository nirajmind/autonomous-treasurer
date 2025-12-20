import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EmailService")

class EmailService:
    def __init__(self):
        # Configs strictly from Environment Variables
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.target_email = os.getenv("ALERT_TARGET_EMAIL")

    def send_alert(self, issue_type, details):
        """
        Sends an HTML formatted email alert.
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ SMTP Credentials missing in .env. Email skipped.")
            return False

        try:
            logger.info(f"📧 Connecting to SMTP Server to alert {self.target_email}...")
            
            subject = f"🚨 TREASURY ALERT: {issue_type}"
            body = f"""
            <html>
              <body>
                <h2>🤖 Autonomous Treasurer Alert</h2>
                <p><strong>Status:</strong> <span style="color:red;">PAUSED</span></p>
                <p><strong>Reason:</strong> {issue_type}</p>
                <p><strong>Technical Details:</strong><br>{details}</p>
                <hr>
                <p><em>Please verify treasury funds immediately.</em></p>
              </body>
            </html>
            """

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.target_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            # Secure SMTP Connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ Email Alert sent successfully.")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False