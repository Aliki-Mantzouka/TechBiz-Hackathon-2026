# Hackathon
# 🤖 Multi-Channel HITL Gateway

### *Human-in-the-Loop Governance for AI Agents*

Ένα ολοκληρωμένο σύστημα **Human-in-the-Loop (HITL)** που επιτρέπει σε AI Agents να ζητούν ανθρώπινη έγκριση μέσω πολλαπλών διαδραστικών καναλιών (**Discord**, **ntfy**, **Email**). Το σύστημα διασφαλίζει το **Governance** και το **Audit Trail** σε κρίσιμες επιχειρηματικές αποφάσεις.

---

## 📋 Προϋποθέσεις (Prerequisites)

Για την επιτυχή εκτέλεση του project, πρέπει να τηρούνται τα εξής:

### 1. Περιβάλλον Λογισμικού
* **Python 3.10+**: Απαιτείται εγκατάσταση σε εικονικό περιβάλλον (venv).
* **Εξαρτήσεις**: Εγκαταστήστε τα απαραίτητα πακέτα: `fastapi`, `uvicorn`, `sqlmodel`, `httpx`.

### 2. Υποδομή Δικτύου (ngrok)
* **Verified Account**: Απαιτείται λογαριασμός στο **ngrok** και εγκατάσταση του Authtoken.
* **Active Tunneling**: Το ngrok πρέπει να τρέχει στην πόρτα **8001** (`ngrok http 8001`) για να είναι προσβάσιμα τα διαδραστικά κουμπιά από εξωτερικά δίκτυα.

### 3. Ρυθμίσεις Καναλιών Επικοινωνίας
* **Discord**: Ένα ενεργό Webhook URL για την αποστολή μηνυμάτων με masked links.
* **ntfy (Mobile)**: Εγγραφή σε topics (π.χ. `eva04`) για λήψη push notifications με **Action Buttons** στο κινητό.
* **Email (Gmail)**: Χρήση **16-ψήφιου App Password** (όχι του κανονικού κωδικού) για την αποστολή διαδραστικών HTML emails.

---
<<<<<<< HEAD
![Hackathon-Email](images/hackathon-email.gif)
![Hackathon NTFY](images/hackathon-ntfy.gif)
![Hachathon Discord](images/hackathon-discord.gif)
=======
![Hackathon-Email](/hackathon/images/hackathon-email.gif)
![Hackathon NTFY](/hackathon/images/hackathon-ntfy.gif)
![Hachathon Discord](/hackathon/images/hackathon-discord.gif)
>>>>>>> 82ad616d514a41143ec6ab54631c98ca90515581
