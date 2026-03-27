from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import Optional
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import engine, HITLTask

router = APIRouter(prefix="/hitl-v2", tags=["HITL Engine"])

BASE_URL = "https://duteously-postsymphysial-shad.ngrok-free.dev"

# EMAIL SETTINGS 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "evavioleti04@gmail.com"
SENDER_PASSWORD = "rvgm psaf yxod geqz" 
ADMIN_EMAIL = "manager-email@example.com"

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with Session(engine) as session:
        tasks = session.exec(select(HITLTask)).all()
    
    rows = ""
    for t in tasks:
        color = "#2ecc71" if t.status == "approved" else "#e74c3c" if t.status == "rejected" else "#f39c12"
        rows += f"""<tr style="border-bottom: 1px solid #ddd;">
            <td style="padding:10px;">{t.id}</td>
            <td style="padding:10px;">{t.agent_id}</td>
            <td style="padding:10px;">{t.context}</td>
            <td style="padding:10px; color:{color}; font-weight:bold;">{t.status.upper()}</td>
        </tr>"""
    return f"<html><body style='font-family:Arial; padding:40px;'><h2>📊 HITL Dashboard</h2><table style='width:100%; border-collapse:collapse;' border='1'>{rows}</table></body></html>"

@router.get("/respond/{task_id}", response_class=HTMLResponse)
async def advanced_respond(task_id: int, decision: str):
    """Το endpoint που καλούν τα κουμπιά του Discord"""
    with Session(engine) as session:
        task = session.get(HITLTask, task_id)
        if not task:
            return "<html><body><h2>Task Not Found</h2></body></html>"
        
        task.status = decision
        session.add(task)
        session.commit()
        session.refresh(task)

        if task.callback_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(task.callback_url, json={"task_id": task_id, "decision": decision})
                except: pass

        color = "#27ae60" if decision == "approved" else "#c0392b"
        return f"""
        <html><body style="text-align:center; padding-top:50px; font-family:Arial;">
            <h1 style="color:{color};">{decision.upper()}!</h1>
            <p>Το Task #{task_id} ενημερώθηκε. Ο Agent ειδοποιήθηκε.</p>
        </body></html>"""

def get_discord_buttons(task_id: int):
    # Αυτά τα links καλούν το endpoint που ήδη έχουμε στο hitl_engine
    approve_link = f"{BASE_URL}/hitl-v2/respond/{task_id}?decision=approved"
    reject_link = f"{BASE_URL}/hitl-v2/respond/{task_id}?decision=rejected"
    
    return approve_link, reject_link
