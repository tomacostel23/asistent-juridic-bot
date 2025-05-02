import os
import logging
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Încarcă variabilele din .env
load_dotenv()

# Variabile de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY")
GOOGLE_CLIENT_EMAIL = os.getenv("GOOGLE_CLIENT_EMAIL")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_PRIVATE_KEY starts with: {GOOGLE_PRIVATE_KEY[:30]}")

# Pregătim credențialele Google
creds_dict = {
    "type": "service_account",
    "project_id": GOOGLE_PROJECT_ID,
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": GOOGLE_PRIVATE_KEY,
    "client_email": GOOGLE_CLIENT_EMAIL,
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
}

# 🔄 Reparăm cheia privată
raw_private_key = creds_dict.get("private_key", "")
logger.info(f"DEBUG: RAW PRIVATE_KEY starts with: {raw_private_key[:30]}")

# 1️⃣ SCOATEM ghilimelele duble dacă există
clean_key = raw_private_key.strip('"').strip("'")

# 2️⃣ Transformăm \\n în linii noi reale
fixed_private_key = clean_key.replace("\\n", "\n")

# 3️⃣ SCOATEM spațiile inutile
fixed_private_key = fixed_private_key.strip()

creds_dict["private_key"] = fixed_private_key
logger.info(f"DEBUG: FIXED PRIVATE_KEY starts with: {creds_dict['private_key'][:30]}")

# Conectare Google Sheets
try:
    creds = Credentials.from_service_account_info(creds_dict)
    gc = gspread.authorize(creds)
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    gc = None

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Folosește comanda /trimite_contract pentru a începe.")

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return

    try:
        sh = gc.open("CONTRACTE")
        worksheet = sh.sheet1
        contracte = worksheet.col_values(1)[1:]  # exclude header-ul

        if not contracte:
            await update.message.reply_text("Nu există contracte disponibile.")
            return

        keyboard = [
            [InlineKeyboardButton(text=contract, callback_data=contract)]
            for contract in contracte
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📄 Selectează contractul dorit:", reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_contract = query.data

    # Salvăm selecția temporar în context pentru confirmare
    context.user_data["selected_contract"] = selected_contract

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Da", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Nu", callback_data="confirm_no"),
        ]
    ])
    await query.edit_message_text(
        text=f"Ai selectat: *{selected_contract}*.\n\nVrei să continui?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":
        contract = context.user_data.get("selected_contract", "necunoscut")
        await query.edit_message_text(
            text=f"✅ Contractul *{contract}* va fi trimis către client.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            text="❌ Ai anulat trimiterea contractului."
        )

# Main app
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
