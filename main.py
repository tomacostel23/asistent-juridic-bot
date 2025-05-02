import logging
import os
import json

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Setările de bază pentru logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Citim tokenul și cheia din variabilele de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Setăm ID-ul foii de calcul și range-ul corect
SPREADSHEET_ID = "1U-i56_v6Hm92Goh7T6lzoZlLfcqaS9UVfb-lWWxwm_w"
RANGE_NAME = "Sheet1!B:B"  # <-- înlocuiește Sheet1 cu numele foii tale dacă e diferit

# Inițializăm Google Sheets API
try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    if "private_key" in creds_dict:
        logger.info("🔧 Am găsit 'private_key', fac replace pentru \\n -> newlines")
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    sheet = None

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Trimite comanda /trimite_contract pentru a continua.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Comanda /trimite_contract primită.")
    if sheet is None:
        await update.message.reply_text("❌ Nu mă pot conecta la Google Sheets.")
        return

    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        contracte = [row[0] for row in values if row and row[0].strip() != ""]
        logger.info(f"✅ Am găsit {len(contracte)} contracte: {contracte}")

        if not contracte:
            await update.message.reply_text("⚠️ Nu am găsit contracte în fișă.")
            return

        reply_markup = ReplyKeyboardMarkup(
            [[contract] for contract in contracte], one_time_keyboard=True, resize_keyboard=True
        )

        await update.message.reply_text(
            "📄 Lista contracte:\nSelectează unul dintre următoarele:",
            reply_markup=reply_markup,
        )

    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor din Google Sheets.")

# Pornirea aplicației
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

if __name__ == "__main__":
    main()

