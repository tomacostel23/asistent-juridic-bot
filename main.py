import os
import logging
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configurare log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Citim variabilele din env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN[:10]}...")

# Convertim JSON-ul de la env
try:
    creds_data = json.loads(GOOGLE_CREDS_JSON)
    logger.info("✅ JSON loaded cu SUCCES direct (fără replace())")

    if 'private_key' in creds_data:
        logger.info("🔧 Am găsit 'private_key', fac replace pentru \\n -> newlines")
        creds_data['private_key'] = creds_data['private_key'].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(
        creds_data,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=creds)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    service = None

# ID-ul și RANGE-ul Google Sheets
SPREADSHEET_ID = "1U-i56_v6Hm92Goh7T6lzoZlLfcqaS9UVfb-lWWxwm_w"
RANGE_NAME = "B:B"

# Comanda: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Trimite comanda /trimite_contract ca să vezi lista de contracte.")

# Comanda: /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Comanda /trimite_contract primită.")

    if service is None:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return

    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            await update.message.reply_text("📄 Nu am găsit contracte.")
            return

        # Extragem doar denumirile din coloana B (fără header gol dacă există)
        contracts = [row[0] for row in values if row and row[0].strip()]

        if not contracts:
            await update.message.reply_text("📄 Lista contractelor este goală.")
            return

        reply_keyboard = [[contract] for contract in contracts]
        await update.message.reply_text(
            "📄 Lista contracte:\nSelectează unul dintre următoarele:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

# Pornirea botului
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

