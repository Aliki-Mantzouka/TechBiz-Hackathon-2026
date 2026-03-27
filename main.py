from datetime import datetime
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel
from pydantic import BaseModel
import httpx
import smtplib
from email.mime.text import MIMEText
from typing import Optional
from email.mime.multipart import MIMEMultipart

# --- ΕΙΣΑΓΩΓΗ ΑΠΟ ΤΑ ΔΙΚΑ ΣΟΥ ΑΡΧΕΙΑ ---
from ntfy import broadcast_to_ntfy
from database import engine, HITLTask

app = FastAPI(title="Multi-Channel HITL Gateway")

# --- ΡΥΘΜΙΣΕΙΣ EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "evavioleti04@gmail.com"
SENDER_PASSWORD = "rvgm psaf yxod geqz"

# Δημιουργία πινάκων στην εκκίνηση
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Μοντέλο για το Swagger
class NotificationInput(BaseModel):
    agent_id: str
    context: str
    urgency: str

# ΡΥΘΜΙΣΕΙΣ DISCORD
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1487051436456939620/usdfzS6VGQ2cbGtJsGlP5MblxJdcWiN58QNkGBTwGn6ivn-aIffdXJVrnmVvzbEZ3yrc"

# --- ΣΥΝΑΡΤΗΣΗ ΑΠΟΣΤΟΛΗΣ EMAIL ---
async def send_approval_email(agent_id: str, context: str, task_id: int, receiver_email: str, base_url: str):
    subject = f"🚨 HITL Action Required (ID: {task_id})"
    # Δημιουργία των links για τα κουμπιά
    approve_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=approved"
    reject_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=rejected"

    # Δημιουργία του HTML σώματος με τα κουμπιά
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Νέο Αίτημα Έγκρισης</h2>
        <p>Ο Agent <b>{agent_id}</b> ζητάει έγκριση για το εξής:</p>
        <blockquote style="background: #f4f4f4; padding: 10px; border-left: 5px solid #ccc;">
            {context}
        </blockquote>
        <div style="margin-top: 20px;">
            <a href="{approve_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">✅ APPROVE</a>
            <a href="{reject_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">❌ REJECT</a>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
            print(f"✅ Email sent to {receiver_email}")
            return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False
    

# --- 1. DISCORD SECTION ---
@app.post("/discord/send", tags=["Discord"])
async def send_to_discord(data: NotificationInput):
    with Session(engine) as session:
        new_task = HITLTask(agent_id=data.agent_id, context=data.context, urgency=data.urgency)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        msg_content = f"👾 **Discord Alert**\n**Agent:** {new_task.agent_id}\n**Context:** {new_task.context}\n**Task ID:** {new_task.id}"
    
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": msg_content})
    return {"status": "Sent to Discord", "task_id": new_task.id}

# --- 2. NTFY (MOBILE) SECTION ---
@app.post("/ntfy/send", tags=["NTFY (Mobile)"])
async def send_to_ntfy(data: NotificationInput):
    with Session(engine) as session:
        new_task = HITLTask(agent_id=data.agent_id, context=data.context, urgency=data.urgency)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)

    await broadcast_to_ntfy(new_task.agent_id, new_task.context, new_task.id)
    return {"status": "Sent to Mobile", "task_id": new_task.id}

# --- 3. EMAIL SECTION ---
@app.post("/email/send", tags=["Email"])
async def send_to_email(data: NotificationInput, target_email: str):
    with Session(engine) as session:
        new_task = HITLTask(
            agent_id=data.agent_id, 
            context=data.context, 
            urgency=data.urgency,
            status="pending"
        )
        session.add(new_task)
        session.commit()
        session.refresh(new_task) # Εδώ η SQLModel μας δίνει το πραγματικό new_task.id

    # 2. Στέλνουμε το email χρησιμοποιώντας το πραγματικό ID
    success = await send_approval_email(
        agent_id=new_task.agent_id,
        context=new_task.context,
        task_id=new_task.id,      # ΤΟ ΠΡΑΓΜΑΤΙΚΟ ID ΑΠΟ ΤΗ ΒΑΣΗ
        receiver_email=target_email,
        base_url=BASE_URL
    )
    
    if success:
        return {
            "status": "Email sent successfully", 
            "task_id": new_task.id, 
            "info": "Check your inbox for the buttons!"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")

# --- 4. MANAGEMENT SECTION ---
@app.post("/hitl/respond/{task_id}", tags=["Management"])
async def human_respond(task_id: int, decision: str):
    with Session(engine) as session:
        task = session.get(HITLTask, task_id)
        if not task: 
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = decision
        session.add(task)
        session.commit()
        session.refresh(task)

        # Έλεγχος για callback αν υπάρχει στο μοντέλο σου
        if hasattr(task, 'callback_url') and task.callback_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(task.callback_url, json={"task_id": task_id, "decision": decision})
                except Exception as e:
                    print(f"Callback failed: {e}")
        
        return {"message": f"Task {task_id} status updated to {decision}", "status": task.status}

from hitl_engine import router as hitl_router
app.include_router(hitl_router)

from hitl_engine import get_discord_buttons, BASE_URL

@app.post("/hitl/request", tags=["Discord 1"])
async def create_hitl_request(task: HITLTask):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        
        app_url, rej_url = get_discord_buttons(task.id)
        
        # Smart Routing Logic
        # 1. Πάντα στο Discord με Buttons
        discord_msg = {
            "content": f"🚨 **New HITL Request** (#{task.id})\n"
                       f"**Agent:** `{task.agent_id}`\n"
                       f"**Context:** {task.context}\n\n"
                       f"✅ [APPROVE]({app_url})  |  ❌ [REJECT]({rej_url})"
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(DISCORD_WEBHOOK_URL, json=discord_msg)
            
            # 2. Αν είναι High Urgency, στείλε ΚΑΙ στο Mobile (ntfy)
            if task.urgency.lower() == "high":
                await broadcast_to_ntfy(
                    task.agent_id,
                    task.context, 
                    task_id=task.id, 
                    base_url=BASE_URL
                )
    return {"status": "dispatched", "task_id": task.id}
# Ενσωμάτωση εξωτερικού router
try:
    from hitl_engine import router as hitl_router
    app.include_router(hitl_router)
except ImportError:
    print("hitl_engine.py not found, skipping router inclusion.")
