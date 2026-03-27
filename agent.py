from fastapi import FastAPI, Request
import uvicorn

app = FastAPI(title="AI Agent Simulator")

@app.post("/agent/callback")
async def receive_callback(request: Request):
    """
    Αυτό το endpoint θα το 'χτυπήσει' ο Gateway (8001) 
    μόλις ο άνθρωπος πατήσει Approve ή Reject.
    """
    data = await request.json()
    
    task_id = data.get("task_id")
    decision = data.get("decision")
    feedback = data.get("feedback", "No feedback")

    print(f"\n" + "="*40)
    print(f"🚀 [AGENT NOTIFICATION] Λήψη απόφασης για το Task #{task_id}")
    print(f"📢 ΑΠΟΦΑΣΗ: {decision.upper()}")
    print(f"📝 FEEDBACK: {feedback}")
    print(f"✅ Ο Agent συνεχίζει τη ροή του βάσει της έγκρισης.")
    print("="*40 + "\n")

    return {"status": "Agent successfully resumed execution"}

if __name__ == "__main__":
    print("🤖 AI Agent Simulator is starting on port 8002...")
    # Τρέχουμε τον Agent στην πόρτα 8002 για να μην μπερδεύεται με τον Gateway (8001)
    uvicorn.run(app, host="127.0.0.1", port=8002)