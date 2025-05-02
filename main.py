import os
import json
import logging
import gspread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# Configurare logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Încarcă variabilele de mediu
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Conectare la Google Sheets cu fallback pentru probleme de \n
try:
    creds_raw = GOOGLE_CREDS_JSON
    logger.info(f"DEBUG: RAW creds starts with: {creds_raw[:50]}")

    # Convertim escape sequences dacă există dublu backslash
    creds_fixed = creds_raw.encode().decode('unicode_escape')
    logger.info(f"DEBUG: FIXED creds starts with: {creds_fixed[:50]}")

    creds_dict = json.loads(creds_fixed)
    gc = gspread.service_account_from_dict(creds_dict)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    gc = None  # prevenim crash-ul aplicației dacă nu e conectat

# Comandă simplă de testare
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Bot-ul este activ. ✅")

async def test_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Nu sunt conectat la Google Sheets.")
        return

    try:
        # Test: listăm fișierele
        sheets = gc.list_spreadsheet_files()
        if sheets:
            lista = "\n".join([f"- {sheet['name']}" for sheet in sheets])
            await update.message.reply_text(f"✅ Fișiere găsite:\n{lista}")
        else:
            await update.message.reply_text("✅ Conectat, dar nu am găsit fișiere.")
    except Exception as e:
        await update.message.reply_text(f"❌ Eroare la citire: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_google", test_google))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
