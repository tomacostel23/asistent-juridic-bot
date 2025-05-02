import os
import json
import logging
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# Configurare logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Încarcă variabilele din .env (dacă folosești local)
load_dotenv()

# Obține variabilele de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Asigură-te că ai acest env setat

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:30]}")

# Conectare la Google Sheets
try:
    creds_json_raw = GOOGLE_CREDS_JSON
    logger.info(f"DEBUG: RAW creds starts with: {creds_json_raw[:30]}")
    creds_json_fixed = creds_json_raw.replace('\\n', '\n')
    logger.info(f"DEBUG: FIXED creds starts with: {creds_json_fixed[:30]}")

    creds_dict = json.loads(creds_json_fixed)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    sheets_service = build('sheets', 'v4', credentials=credentials)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    sheets_service = None

# Comandă: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Sunt gata să te ajut cu contractele.")

# Comandă: /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheets_service is None:
        await update.message.reply_text("❌ Nu mă pot conecta la Google Sheets.")
        return

    try:
        sheet = sheets_service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Contracte!A2:B"  # presupunem că datele sunt în coloanele A și B
        ).execute()
        values = result.get('values', [])

        if not values:
            await update.message.reply_text("❌ Nu am găsit contracte.")
            return

        contracte = [row[1] for row in values if len(row) > 1]
        lista_contracte = '\n'.join(f"- {c}" for c in contracte)
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in contracte],
            one_time_keyboard=True,
            resize_keyboard=True
        )

        await update.message.reply_text(
            f"📄 Lista contracte:\nSelectează unul dintre următoarele:\n\n{lista_contracte}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ A apărut o eroare la citirea contractelor.")

# Handler pentru confirmare da/nu
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raspuns = update.message.text.lower()
    if raspuns == "da":
        await update.message.reply_text("✅ Ai confirmat cu 'da'.")
    elif raspuns == "nu":
        await update.message.reply_text("❌ Ai răspuns 'nu'. Operațiunea a fost anulată.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^(da|nu)$"), handle_confirmation))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
