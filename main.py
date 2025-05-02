import logging
import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Debug ENV vars
logging.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logging.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Scriem într-un fișier pt. verificare manuală (opțional)
with open("debug_creds.json", "w") as f:
    f.write(GOOGLE_CREDS_JSON)

# ✅ Încărcăm direct JSON-ul (fără replace)
try:
    creds_info = json.loads(GOOGLE_CREDS_JSON)
    logging.info("✅ JSON loaded cu SUCCES direct (fără replace())")
except json.JSONDecodeError as e:
    logging.error(f"❌ Eroare la JSON direct: {e}")
    raise SystemExit(1)

# Conectare la Google Sheets
try:
    creds = Credentials.from_service_account_info(creds_info)
    service = build('sheets', 'v4', credentials=creds)
    logging.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logging.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    raise SystemExit(1)

# Exemplu de comanda simplă
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Bot-ul este online și conectat la Google Sheets.")

if TELEGRAM_TOKEN:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logging.info("🚀 Bot-ul rulează...")
    app.run_polling()
else:
    logging.error("❌ TELEGRAM_TOKEN lipsește!")
