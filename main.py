from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, SQLModel, select
from pydantic import BaseModel
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# --- ΕΙΣΑΓΩΓΗ ΑΠΟ ΤOΠΙΚΑ ΑΡΧΕΙΑ ---
from ntfy import broadcast_to_ntfy
from database import engine, HITLTask
from fastapi.templating import Jinja2Templates
from hitl_engine import get_discord_buttons, BASE_URL

# Ορισμός φακέλου για τα HTML αρχεία
templates = Jinja2Templates(directory="templates")

app = FastAPI(title="Multi-Channel HITL Gateway")

# --- ΡΥΘΜΙΣΕΙΣ ---
SENDER_EMAIL = "evavioleti04@gmail.com"
SENDER_PASSWORD = "rvgm psaf yxod geqz"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1487051436456939620/usdfzS6VGQ2cbGtJsGlP5MblxJdcWiN58QNkGBTwGn6ivn-aIffdXJVrnmVvzbEZ3yrc"

# Δημιουργία πινάκων στην εκκίνηση
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Μοντέλο για το Swagger
class NotificationInput(BaseModel):
    agent_id: str
    context: str
    urgency: str

# --- ΣΥΝΑΡΤΗΣΗ ΑΠΟΣΤΟΛΗΣ EMAIL ---
async def send_approval_email(agent_id: str, context: str, task_id: int, receiver_email: str, base_url: str):
    subject = f"🚨 HITL Action Required (ID: {task_id})"
    base_url = base_url.rstrip("/")
    
    # Links για τα κουμπιά
    approve_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=approved"
    reject_url = f"{base_url}/hitl-v2/respond/{task_id}?decision=rejected"

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

# --- 1. EMAIL SECTION ---
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
        session.refresh(new_task)

    success = await send_approval_email(
        agent_id=new_task.agent_id,
        context=new_task.context,
        task_id=new_task.id,
        receiver_email=target_email,
        base_url=BASE_URL
    )
    
    if success:
        return {"status": "Email sent successfully", "task_id": new_task.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
@app.post("/ntfy/send", tags=["NTFY (Mobile)"])
async def send_to_ntfy_standalone(data: NotificationInput):
    with Session(engine) as session:
        new_task = HITLTask(
            agent_id=data.agent_id, 
            context=data.context, 
            urgency=data.urgency,
            status="pending"
        )
        session.add(new_task)
        session.commit()
        session.refresh(new_task)

    # Καλούμε τη συνάρτηση από το ntfy.py
    await broadcast_to_ntfy(
        new_task.agent_id, 
        new_task.context, 
        task_id=new_task.id, 
        base_url=BASE_URL
    )
    
    return {"status": "Sent to Mobile", "task_id": new_task.id}

# --- 2. MULTI-CHANNEL REQUEST (DISCORD + NTFY) ---
@app.post("/hitl/request", tags=["HITL Main"])
async def create_hitl_request(task: HITLTask):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        
        app_url, rej_url = get_discord_buttons(task.id)
        
        # 1. Πάντα στο Discord
        discord_msg = {
            "content": f"🚨 **New HITL Request** (#{task.id})\n"
                       f"**Agent:** `{task.agent_id}`\n"
                       f"**Context:** {task.context}\n\n"
                       f"✅ [APPROVE]({app_url})  |  ❌ [REJECT]({rej_url})"
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(DISCORD_WEBHOOK_URL, json=discord_msg)
            
            # 2. Αν είναι High Urgency, στείλε και Mobile (ntfy)
            if task.urgency.lower() == "high":
                await broadcast_to_ntfy(
                    task.agent_id,
                    task.context, 
                    task_id=task.id, 
                    base_url=BASE_URL
                )
    return {"status": "dispatched", "task_id": task.id}

# --- 3. DASHBOARD & MANAGEMENT ---
@app.get("/hitl-v2/dashboard", response_class=HTMLResponse, tags=["HITL Engine"])
async def get_dashboard(request: Request):
    with Session(engine) as session:
        tasks = session.exec(select(HITLTask)).all()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})

# Ενσωμάτωση Router από hitl_engine
try:
    from hitl_engine import router as hitl_router
    app.include_router(hitl_router)
except ImportError:
    print("hitl_engine router not found.")