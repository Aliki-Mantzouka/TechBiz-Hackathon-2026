from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
import httpx

# Κάνουμε import το engine και το HITLTask από το main για να χρησιμοποιούμε την ίδια βάση
from database import engine, HITLTask

router = APIRouter(prefix="/hitl-v2", tags=["HITL Engine"])

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Ζωντανός πίνακας για το Audit Trail (ThinkBiz 2026 Requirement)"""
    with Session(engine) as session:
        tasks = session.exec(select(HITLTask)).all()
    
    rows = ""
    for t in tasks:
        color = "#2ecc71" if t.status == "approved" else "#e74c3c" if t.status == "rejected" else "#f39c12"
        rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding:10px;">{t.id}</td>
            <td style="padding:10px;">{t.agent_id}</td>
            <td style="padding:10px;">{t.context}</td>
            <td style="padding:10px; color:{color}; font-weight:bold;">{t.status.upper()}</td>
        </tr>"""

    return f"""
    <html>
        <body style="font-family:Arial; padding:40px; background:#f9f9f9;">
            <div style="background:white; padding:20px; border-radius:10px; shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color:#2c3e50;">📊 HITL Gateway Dashboard</h2>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="background:#2c3e50; color:white;">
                        <th style="padding:10px; text-align:left;">ID</th>
                        <th style="padding:10px; text-align:left;">Agent</th>
                        <th style="padding:10px; text-align:left;">Context</th>
                        <th style="padding:10px; text-align:left;">Status</th>
                    </tr>
                    {rows}
                </table>
            </div>
        </body>
    </html>"""

@router.post("/respond/{task_id}")
async def advanced_respond(task_id: int, decision: str, feedback: Optional[str] = None):
    """Η εξελιγμένη Respond που κάνει το Callback στον Agent (Closing the Loop)"""
    with Session(engine) as session:
        task = session.get(HITLTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = decision
        session.add(task)
        session.commit()
        session.refresh(task)

        # Webhook Callback: Ενημέρωση του Agent (Port 8002)
        if hasattr(task, 'callback_url') and task.callback_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(task.callback_url, json={
                        "task_id": task_id, 
                        "decision": decision, 
                        "feedback": feedback
                    })
                except Exception as e:
                    print(f"Callback Failed: {e}")

        return {"status": "success", "task_id": task_id, "agent_notified": True}