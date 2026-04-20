import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading

def send_faculty_email_async(subject, body, to_email='soumyasubhradatta@gmail.com'):
    """Sends an email asynchronously to avoid blocking the API response."""
    def send():
        sender_email = os.environ.get('SMTP_EMAIL')
        sender_password = os.environ.get('SMTP_PASSWORD')
        
        if not sender_email or not sender_password:
            print("[Email] SMTP credentials not configured. Skipping email.")
            return

        msg = MIMEMultipart()
        msg['From'] = f"SIST Faculty Portal <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = f"[Faculty Portal] {subject}"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #c0392b;">Sathyabama Institute of Science and Technology</h2>
                <h3>Faculty Duty Notification</h3>
                <p>{body}</p>
                <br>
                <p style="font-size: 0.85rem; color: #777;">
                    This is an automated message from the Faculty Workload Scheduling and Substitution Portal.
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        try:
            # Using Gmail SMTP by default
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"[Email] Successfully sent email for '{subject}'")
        except Exception as e:
            error_str = str(e)
            if 'BadCredentials' in error_str or 'Username and Password not accepted' in error_str:
                print("[Email] Invalid SMTP credentials. Please check SMTP_EMAIL and SMTP_PASSWORD in .env file.")
            else:
                print(f"[Email] Failed to send email: {error_str}")

    thread = threading.Thread(target=send)
    thread.start()
