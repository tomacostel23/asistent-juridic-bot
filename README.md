📄 Asistent Juridic Bot
Un bot Telegram inteligent care automatizează procesul de trimitere a contractelor juridice către clienți. Botul permite selectarea unui contract dintr-o listă (citită din Google Sheets), colectarea datelor destinatarului (nume + email) și, în pasul următor, trimiterea formularului pentru completare.

🚀 Funcționalități:
✅ Comandă /start – Mesaj de întâmpinare.

✅ Comandă /trimite_contract:

Citește lista de contracte din Google Sheets.

Afișează lista contractelor disponibile.

Întreabă numele persoanei/instituției destinatare.

Întreabă adresa de email.

(În dezvoltare) Trimite email automat cu formularul Google Forms aferent contractului.

✅ (În dezvoltare) Verifică statusul completării formularului.

🛠️ Tehnologii utilizate:
Python 3

python-telegram-bot

gspread

Google Sheets API

📦 Instalare locală:
1️⃣ Clonează repo-ul:

bash
Copy
Edit
git clone https://github.com/USERNAME/NUME_REPO.git
cd NUME_REPO
2️⃣ Instalează dependențele:

bash
Copy
Edit
pip install -r requirements.txt
3️⃣ Creează un fișier .env (sau setează variabilele de mediu) cu următoarele:

ini
Copy
Edit
TELEGRAM_BOT_TOKEN=tokenul_tău_telegram
SHEET_NAME=numele_fișierului_google_sheet
GOOGLE_CREDS_JSON=conținutul_complet_al_service_account_json
🚀 Deploy pe Railway:
1️⃣ Leagă repo-ul GitHub la Railway.

2️⃣ În Settings > Variables, adaugă:

Nume	Valoare
TELEGRAM_BOT_TOKEN	Tokenul botului tău Telegram (de la BotFather)
SHEET_NAME	Numele Google Sheet-ului tău (ex: Asistent Juridic Contracte)
GOOGLE_CREDS_JSON	Conținutul complet al fișierului service_account.json (pe o linie)

3️⃣ Deploy automat ✅.

📝 Structura Google Sheet:
Coloana 1 (ID)	Coloana 2 (Nume contract)	Coloana 3 (Link Google Form)	Coloana 4 (Link Google Sheet cu răspunsuri)
1	Contract Credit	https://forms.gle/...	https://docs.google.com/spreadsheets/...
2	Contract Consultanță	https://forms.gle/...	https://docs.google.com/spreadsheets/...

🔑 IMPORTANT: Partajează fișierul Google Sheets cu adresa service account-ului tău (ex: asistent-bot@...iam.gserviceaccount.com), cu drepturi de Editor.

✅ Comenzi disponibile:
/start – Mesaj de întâmpinare.

/trimite_contract – Pornește procesul de trimitere contract.

✨ În dezvoltare:
Trimiterea automată a emailului cu formularul.

Verificarea automată a completării formularului.

Suport AI/NLP pentru comenzi flexibile în limbaj natural.

🤝 Contribuții:
PR-urile și sugestiile sunt binevenite! 😊

📄 Licență:
MIT License.
