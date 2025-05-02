import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
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

# Dict pentru stocare temporară a stării per user
user_data = {}

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Comanda /trimite_contract primită.")
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        logger.info(f"DEBUG: Am citit {len(values)} rânduri din Sheets.")
        contracte = [row[0] for row in values if row and row[0].strip()]
        
        if contracte and contracte[0].lower() in ["denumire", "nume contract"]:
            logger.info("🔎 Am detectat cap de tabel, îl ignor.")
            contracte = contracte[1:]

        if not contracte:
            await update.message.reply_text("⚠️ Nu am găsit niciun contract disponibil.")
            return

        # Creăm butoane inline
        keyboard = [
            [InlineKeyboardButton(contract, callback_data=f"contract|{contract}")]
            for contract in contracte
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        mesaj = "📄 Lista contracte:\nSelectează unul dintre următoarele:"
        await update.message.reply_text(mesaj, reply_markup=reply_markup)
        logger.info(f"✅ Am trimis lista cu {len(contracte)} contracte (cu butoane).")

    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ A apărut o eroare la citirea contractelor. Încearcă din nou mai târziu.")

# Handler pentru selectarea contractului
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # Când alegi un contract
    if data.startswith("contract|"):
        contract_name = data.split("|", 1)[1]
        user_data[user_id] = {"contract": contract_name}

        logger.info(f"🖱️ Utilizatorul a selectat contractul: {contract_name}")

        # Butoane DA / NU
        keyboard = [
            [
                InlineKeyboardButton("✅ DA", callback_data="confirm|da"),
                InlineKeyboardButton("❌ NU", callback_data="confirm|nu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        mesaj = (
            f"✅ Ai selectat contractul:\n\n📄 {contract_name}\n\n"
            "Dorești să continui cu acest contract?"
        )
        await query.edit_message_text(mesaj, reply_markup=reply_markup)

    # Confirmare DA / NU
    elif data.startswith("confirm|"):
        choice = data.split("|", 1)[1]
        if choice == "nu":
            await query.edit_message_text("🚫 Selecția a fost anulată.")
            user_data.pop(user_id, None)
        elif choice == "da":
            await query.edit_message_text("📨 Introdu numele persoanei/companiei către care dorești să trimiți contractul.")
            user_data[user_id]["awaiting_name"] = True

# Handler pentru mesaje text (nume & email)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        return  # Ignorăm dacă nu avem stare

    # Dacă așteptăm numele persoanei/companiei
    if user_data[user_id].get("awaiting_name"):
        user_data[user_id]["nume"] = text
        user_data[user_id].pop("awaiting_name")
        user_data[user_id]["awaiting_email"] = True
        await update.message.reply_text(f"✉️ Introdu adresa de email la care să trimit contractul către {text}.")

    # Dacă așteptăm emailul
    elif user_data[user_id].get("awaiting_email"):
        user_data[user_id]["email"] = text
        user_data[user_id].pop("awaiting_email")
        contract = user_data[user_id].get("contract")
        nume = user_data[user_id].get("nume")
        email = user_data[user_id].get("email")

        logger.info(f"📦 Finalizare: Contract: {contract}, Nume: {nume}, Email: {email}")
        await update.message.reply_text(
            f"✅ Am înregistrat următoarele informații:\n\n"
            f"📄 Contract: {contract}\n"
            f"👤 Către: {nume}\n"
            f"✉️ Email: {email}\n\n"
            "🔔 (Aici va urma trimiterea automată a contractului...)"
        )

        # Resetăm starea pentru user
        user_data.pop(user_id)

# Start bot
if __name__ == "__main__":
    logger.info("🚀 Bot-ul rulează...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

