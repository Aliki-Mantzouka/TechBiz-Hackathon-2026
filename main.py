from datetime import datetime
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel
from pydantic import BaseModel
import httpx

# --- ΕΙΣΑΓΩΓΗ ΑΠΟ ΤΑ ΔΙΚΑ ΣΟΥ ΑΡΧΕΙΑ ---
from ntfy import broadcast_to_ntfy
from database import engine, HITLTask

app = FastAPI(title="Multi-Channel HITL Gateway")

# Δημιουργία πινάκων στην εκκίνηση
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Μοντέλο για το Swagger (Μόνο τα πεδία εισόδου)
#mail
#SMTP_SERVER = "smtp.gmail.com"
#SMTP_PORT = 587
#SENDER_EMAIL = "evavioleti04@gmail.com"
#SENDER_PASSWORD = "your-app-password" # Όχι ο κανονικός κωδικός!
#ADMIN_EMAIL = "manager-email@example.com"

# 2. Μοντέλο για το Swagger (Μόνο τα πεδία που θέλεις να συμπληρώνεις)
class NotificationInput(BaseModel):
    agent_id: str
    context: str
    urgency: str

# ΡΥΘΜΙΣΕΙΣ
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1487051436456939620/usdfzS6VGQ2cbGtJsGlP5MblxJdcWiN58QNkGBTwGn6ivn-aIffdXJVrnmVvzbEZ3yrc"

# --- 1. DISCORD SECTION ---
@app.post("/discord/send", tags=["Discord"])
async def send_to_discord(data: NotificationInput):
    """Στέλνει στο Discord και αποθηκεύει στη βάση."""
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
        # Δημιουργούμε το task στη βάση
        new_task = HITLTask(agent_id=data.agent_id, context=data.context, urgency=data.urgency)
        session.add(new_task)
        session.commit()
        session.refresh(new_task) # Παίρνουμε το ID που δημιουργήθηκε

    # Στέλνουμε το ID στο κινητό
    await broadcast_to_ntfy(new_task.agent_id, new_task.context, new_task.id)
    
    return {"status": "Sent to Mobile", "task_id": new_task.id}

# --- Στο endpoint για το Management ---
@app.post("/hitl/respond/{task_id}", tags=["Management"])
async def human_respond(task_id: int, decision: str):
    with Session(engine) as session:
        # Ψάχνουμε το task στη βάση δεδομένων
        task = session.get(HITLTask, task_id)
        if not task: 
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Αλλάζουμε το status από 'pending' σε 'accepted' ή 'refused'
        task.status = decision
        session.add(task)
        session.commit()
        
        return {"message": f"Task {task_id} status updated to {decision}"}

# --- 3. MANAGEMENT (Human-in-the-loop) ---
@app.post("/hitl/respond/{task_id}", tags=["Management"])
async def human_respond(task_id: int, decision: str):
    """Ενημερώνει την απόφαση και εκτελεί το Callback αν υπάρχει."""
    with Session(engine) as session:
        task = session.get(HITLTask, task_id)
        if not task: 
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = decision
        session.add(task)
        session.commit()
        session.refresh(task) # Παίρνουμε το callback_url από τη βάση

        # Λογική Callback (Αυτόματη ενημέρωση του Agent που έστειλε το Task)
        if task.callback_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(task.callback_url, json={
                        "task_id": task_id,
                        "decision": decision
                    })
                except Exception as e:
                    print(f"Callback failed for task {task_id}: {e}")
        
        return {"message": f"Task {task_id} updated to {decision}", "status": task.status}

# Ενσωμάτωση του εξωτερικού router (αν υπάρχει το αρχείο hitl_engine.py)
try:
    from hitl_engine import router as hitl_router
    app.include_router(hitl_router)
except ImportError:
    print("hitl_engine.py not found, skipping router inclusion.")