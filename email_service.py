import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ΡΥΘΜΙΣΕΙΣ ΓΙΑ ΤΟ EMAIL
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "evavioleti04@gmail.com"
SENDER_PASSWORD = "rvgm psaf yxod geqz"

async def send_approval_email(agent_id: str, context: str, task_id: int, receiver_email: str, base_url: str):
    """
    Στέλνει HTML email με κουμπιά Accept/Reject.
    """
    subject = f"🚨 HITL Action Required (ID: {task_id})"
    base_url = base_url.rstrip("/")
    
    # Δημιουργία των Links για τα κουμπιά
    approve_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=approved"
    reject_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=rejected"
    
    # Το HTML σώμα του Email με στυλ για τα κουμπιά
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c3e50;">Human-in-the-Loop Approval</h2>
            <p>Ο Agent <strong>{agent_id}</strong> ζητάει την έγκρισή σου για την εξής ενέργεια:</p>
            <div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #3498db; margin: 20px 0;">
                {context}
            </div>
            <p style="text-align: center; margin-top: 30px;">
                <a href="{approve_url}" style="background-color: #27ae60; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">✅ APPROVE</a>
                <a href="{reject_url}" style="background-color: #e74c3c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">❌ REJECT</a>
            </p>
            <p style="font-size: 12px; color: #7f8c8d; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                Task ID: {task_id} | Multi-Channel HITL Gateway
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD.replace(" ", "")) # Αφαίρεση κενών από το password
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
            print(f"✅ Interactive Email sent to {receiver_email}")
            return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False