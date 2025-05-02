import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Config logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Citim variabilele din env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN[:10]}... (ascuns restul)")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Procesăm credentials
creds_dict = json.loads(GOOGLE_CREDS_JSON)
if "private_key" in creds_dict and "\\n" in creds_dict["private_key"]:
    logger.info("🔧 Am găsit 'private_key', fac replace pentru \\n -> newlines")
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

# Conectare Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)
logger.info("✅ Conectat la Google Sheets.")

# ID și range Google Sheets
SPREADSHEET_ID = "1U-i56_v6Hm92Goh7T6lzoZlLfcqaS9UVfb-lWWxwm_w"
RANGE_NAME = "B:B"  # Coloana cu denumirile contractelor

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Comanda /trimite_contract primită.")
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        logger.info(f"DEBUG: Am citit {len(values)} rânduri din Sheets.")
        # Extragem denumirile reale (fără cap de tabel și rânduri goale)
        contracte = [row[0] for row in values if row and row[0].strip()]
        
        if contracte and contracte[0].lower() in ["denumire", "nume contract"]:
            logger.info("🔎 Am detectat cap de tabel, îl ignor.")
            contracte = contracte[1:]

        if not contracte:
            await update.message.reply_text("⚠️ Nu am găsit niciun contract disponibil.")
            return

        # Creăm butoanele inline
        keyboard = [
            [InlineKeyboardButton(contract, callback_data=contract)]
            for contract in contracte
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        mesaj = "📄 Lista contracte:\nSelectează unul dintre următoarele:"
        await update.message.reply_text(mesaj, reply_markup=reply_markup)
        logger.info(f"✅ Am trimis lista cu {len(contracte)} contracte (cu butoane).")

    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ A apărut o eroare la citirea contractelor. Încearcă din nou mai târziu.")

# Handler pentru când alegi un contract
async def handle_contract_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contract_selectat = query.data
    logger.info(f"🖱️ Utilizatorul a selectat contractul: {contract_selectat}")
    await query.edit_message_text(f"✅ Ai selectat contractul:\n\n📄 {contract_selectat}\n\nDorești să continui cu acest contract? (DA/NU)")

# Start bot
if __name__ == "__main__":
    logger.info("🚀 Bot-ul rulează...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CallbackQueryHandler(handle_contract_select))
    app.run_polling()

