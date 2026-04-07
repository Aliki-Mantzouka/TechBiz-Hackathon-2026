# 🤖 Multi-Channel HITL Gateway

Human-in-the-Loop Governance for AI Agents
A work-in-progress Human-in-the-Loop (HITL) system that enables AI Agents to request human approval via multiple interactive channels (Discord, ntfy, Email). The system ensures Governance and a robust Audit Trail for critical business decisions.

# 📋 Prerequisites
To successfully execute the project, the following must be met:

# 1. Software Environment
Python 3.10+: Installation in a virtual environment (venv) is required.
Dependencies: Install the necessary packages: fastapi, uvicorn, sqlmodel, httpx.

# 2. Network Infrastructure (ngrok)
Verified Account: An ngrok account and Authtoken installation are required.
Active Tunneling: ngrok must be running on port 8001 (ngrok http 8001) so that interactive buttons are accessible from external networks.

# 3. Communication Channel Settings

Email (Gmail): Use of a 16-digit App Password (not the regular account password) for sending interactive HTML emails.
Notify (ntfy): Create a free Notify name (e.g., eva04) to receive push notifications with Action Buttons.
Discord: An active Webhook URL for sending messages with masked links.

Demo videos for Email (Gmail), Notify (ntfy) and Discord:
---
![Hackathon-Email](images/hackathon-email.gif)
![Hackathon NTFY](images/hackathon-ntfy.gif)
![Hachathon Discord](images/hackathon-discord.gif)
