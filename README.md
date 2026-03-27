# Hackathon


🤖 Multi-Channel HITL Gateway
Ένα ολοκληρωμένο σύστημα Human-in-the-Loop (HITL) που επιτρέπει σε AI Agents να ζητούν ανθρώπινη έγκριση μέσω πολλαπλών διαδραστικών καναλιών (Discord, ntfy, Email). Το σύστημα διασφαλίζει το Governance και το Audit Trail σε κρίσιμες επιχειρηματικές αποφάσεις.

📋 Προϋποθέσεις (Prerequisites)
Για την επιτυχή εκτέλεση του project, πρέπει να τηρούνται τα εξής:

1. Περιβάλλον Λογισμικού
Python 3.10+: Απαιτείται εγκατάσταση σε εικονικό περιβάλλον (venv).

Εξαρτήσεις: Εγκαταστήστε τα απαραίτητα πακέτα: fastapi, uvicorn, sqlmodel, httpx.

2. Υποδομή Δικτύου (ngrok)
Verified Account: Απαιτείται λογαριασμός στο ngrok και εγκατάσταση του Authtoken.

Active Tunneling: Το ngrok πρέπει να τρέχει στην πόρτα 8001 (ngrok http 8001) για να είναι προσβάσιμα τα διαδραστικά κουμπιά από εξωτερικά δίκτυα.

3. Ρυθμίσεις Καναλιών Επικοινωνίας
Discord: Ένα ενεργό Webhook URL για την αποστολή μηνυμάτων με masked links.

ntfy (Mobile): Εγγραφή σε topics (π.χ. eva04) για λήψη push notifications με Action Buttons στο κινητό.

Email (Gmail): Χρήση 16-ψήφιου App Password (όχι του κανονικού κωδικού) για την αποστολή διαδραστικών HTML emails.

🚀 Οδηγίες Εγκατάστασης & Εκτέλεσης
Εκκίνηση του Tunnel:

Bash
ngrok http 8001
Αντιγράψτε το https://... URL που θα εμφανιστεί στο πεδίο Forwarding.

Παραμετροποίηση:

Στο αρχείο hitl_engine.py, ενημερώστε τη μεταβλητή BASE_URL με το URL του ngrok.

Στο αρχείο email_service.py, βεβαιωθείτε ότι το SENDER_PASSWORD είναι το σωστό App Password χωρίς κενά.

Εκτέλεση του Gateway:

Bash
uvicorn main:app --reload --port 8001
Εκτέλεση του Agent:
Βεβαιωθείτε ότι ο AI Agent εκτελείται (π.χ. στην πόρτα 8002) για να λαμβάνει τα callbacks των αποφάσεων.

🛠 Τεχνική Αρχιτεκτονική
Persistence: Χρήση SQLite για την αποθήκευση της κατάστασης (Pending/Approved/Rejected) κάθε αιτήματος.

Smart Routing: Αυτόματη κλιμάκωση ειδοποιήσεων. Τα "High Urgency" αιτήματα προωθούνται ταυτόχρονα σε όλα τα κανάλια.

Interactive Approvals: Η έγκριση γίνεται μέσω HTTP GET requests που πυροδοτούνται από τα κουμπιά στις εφαρμογές, ενημερώνοντας άμεσα τη βάση δεδομένων.

Audit Dashboard: Μια web σελίδα που απεικονίζει σε πραγματικό χρόνο το ιστορικό όλων των αλληλεπιδράσεων.