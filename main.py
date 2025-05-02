import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Citim tokenul și cheia JSON din variabilele de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")  # <-- Adaugă ID-ul fișei Google Sheets ca variabilă de mediu

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Configurăm Google Sheets API
sheets_service = None
try:
    raw_creds = GOOGLE_CREDS_JSON
    logger.info(f"DEBUG: RAW creds starts with: {raw_creds[:50]}")
    fixed_creds = raw_creds.replace('\\n', '\n')
    logger.info(f"DEBUG: FIXED creds starts with: {fixed_creds[:50]}")

    creds_dict = json.loads(fixed_creds)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    sheets_service = build("sheets", "v4", credentials=creds)

    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")

# Handler pentru comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Trimite comanda /trimite_contract pentru a vedea lista de contracte.")

# Handler pentru comanda /trimite_contract
async def handle_trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not sheets_service:
            await update.message.reply_text("❌ Nu mă pot conecta la Google Sheets.")
            return

        sheet_id = GOOGLE_SHEET_ID
        range_name = 'A:Z'  # citim tot rândul (presupunem max 26 coloane)

        sheet = sheets_service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
        rows = result.get('values', [])

        if not rows or len(rows) < 2:
            await update.message.reply_text("❌ Nu am găsit niciun contract în Google Sheet.")
            logger.info("📄 Contracte găsite: NIMIC")
            return

        # Presupunem că primul rând e header
        contracts = []
        for row in rows[1:]:
            if len(row) >= 2:
                contracts.append(row[1])  # coloana 2 (index 1)

        if not contracts:
            await update.message.reply_text("❌ Nu am găsit contracte cu denumiri valide.")
            return

        logger.info(f"📄 Contracte găsite: {contracts}")

        message_text = "📄 Lista contracte:\nSelectează unul dintre următoarele:"
        keyboard = [[contract] for contract in contracts]

        await update.message.reply_text(
            message_text,
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )

    except Exception as e:
        logger.error(f"Eroare la citirea contractelor din Google Sheet: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor din Google Sheet.")

# Handler pentru răspunsurile DA/NU (confirmare)
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text.strip().lower()
    if user_response == "da":
        await update.message.reply_text("✅ Ai confirmat trimiterea.")
    elif user_response == "nu":
        await update.message.reply_text("❌ Ai anulat operațiunea.")
    else:
        await update.message.reply_text("❓ Te rog răspunde cu 'da' sau 'nu'.")

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", handle_trimite_contract))
    app.add_handler(MessageHandler(filters.Regex(r"^(?i)da$|^(?i)nu$"), handle_confirmation))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

