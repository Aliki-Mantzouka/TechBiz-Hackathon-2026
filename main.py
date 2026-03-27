from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine
from typing import Optional
from pydantic import BaseModel
import httpx

# 1. Μοντέλο Βάσης Δεδομένων
class HITLTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str
    context: str
    urgency: str
    status: str = "pending"
    callback_url: Optional[str] = None

# 2. Μοντέλο για το Swagger (Μόνο τα πεδία που θέλεις να συμπληρώνεις)
class NotificationInput(BaseModel):
    agent_id: str
    context: str
    urgency: str

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)

app = FastAPI(title="Multi-Channel HITL Gateway")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# ΡΥΘΜΙΣΕΙΣ
NTFY_TOPICS = ["eva04", "nodashackathon"]
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1487051436456939620/usdfzS6VGQ2cbGtJsGlP5MblxJdcWiN58QNkGBTwGn6ivn-aIffdXJVrnmVvzbEZ3yrc"

# --- 1. DISCORD SECTION ---
@app.post("/discord/send", tags=["Discord"])
async def send_to_discord(data: NotificationInput):
    """Στέλνει ΜΟΝΟ στο Discord."""
    with Session(engine) as session:
        # Μετατρέπουμε το input σε HITLTask για τη βάση
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
    """Στέλνει ΜΟΝΟ στο NTFY."""
    with Session(engine) as session:
        new_task = HITLTask(agent_id=data.agent_id, context=data.context, urgency=data.urgency)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        msg_text = f"📱 [Mobile Alert] {new_task.agent_id}: {new_task.context}"

    async with httpx.AsyncClient() as client:
        for topic in NTFY_TOPICS:
            await client.post(f"https://ntfy.sh/{topic}", data=msg_text.encode('utf-8'))
    return {"status": "Sent to Mobile", "task_id": new_task.id}

# --- 3. MANAGEMENT ---
@app.post("/hitl/respond/{task_id}", tags=["Management"])
async def human_respond(task_id: int, decision: str):
    with Session(engine) as session:
        task = session.get(HITLTask, task_id)
        if not task: 
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = decision
        session.add(task)
        session.commit()
        session.refresh(task) # Refresh για να πάρουμε το callback_url

        # --- CALLBACK LOGIC ---
        if task.callback_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(task.callback_url, json={
                        "task_id": task_id,
                        "decision": decision
                    })
                except Exception as e:
                    print(f"Callback failed: {e}")
        
        return {"message": f"Task {task_id} updated to {decision}"}