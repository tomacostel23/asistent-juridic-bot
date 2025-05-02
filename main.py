import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configurare logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Citește token și chei din environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Trebuie să existe în ENV!

# Debug
logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Setare Google Sheets
creds_data = json.loads(GOOGLE_CREDS_JSON)
if 'private_key' in creds_data and '\\n' in creds_data['private_key']:
    logger.info("🔧 Am găsit 'private_key', fac replace pentru \\n -> newlines")
    creds_data['private_key'] = creds_data['private_key'].replace('\\n', '\n')

creds = Credentials.from_service_account_info(creds_data, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

logger.info("✅ Conectat la Google Sheets.")

# Handler pentru /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Sunt asistentul juridic. Trimite comanda /trimite_contract pentru a începe.")

# Handler pentru /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Comanda /trimite_contract primită.")
    try:
        # Citește toate rândurile din Sheet
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="A1:Z1000").execute()
        values = result.get('values', [])

        if not values:
            await update.message.reply_text("❌ Nu am găsit niciun contract.")
            return

        # Extrage contractele din coloana 2 (index 1)
        contracts = []
        for row in values:
            if len(row) > 1 and row[1].strip():  # Asigură că există coloana 2 și nu e goală
                contracts.append(row[1].strip())

        if not contracts:
            await update.message.reply_text("❌ Nu există contracte disponibile.")
            return

        # Creează butoane pentru fiecare contract
        keyboard = [[KeyboardButton(contract)] for contract in contracts]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            "📄 Lista contracte:\nSelectează unul dintre următoarele:",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ A apărut o eroare la citirea contractelor.")

# Handler pentru selecția unui contract
async def handle_contract_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_contract = update.message.text
    logger.info(f"✅ Utilizatorul a selectat contractul: {selected_contract}")
    await update.message.reply_text(f"✅ Ai selectat contractul: *{selected_contract}*.\nDorești să continui?", parse_mode="Markdown")

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))

    # Prinde orice text după alegerea contractului
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contract_selection))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
