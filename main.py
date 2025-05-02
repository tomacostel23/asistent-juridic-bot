import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configurare logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Citire variabile ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Setare Google Sheets
gc = None
try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    logger.info(f"DEBUG: RAW creds starts with: {GOOGLE_CREDS_JSON[:50]}")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")

# Comandă /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Bot-ul este online ✅")

# Comandă /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Extragerea contractelor dintr-un sheet (exemplu)
        sh = gc.open("Numele_Tabelului_Tau")  # Înlocuiește cu numele tabelului tău
        worksheet = sh.sheet1
        contracte = worksheet.col_values(1)[1:]  # Salt peste header

        if not contracte:
            await update.message.reply_text("Nu am găsit contracte.")
            return

        keyboard = [
            [InlineKeyboardButton(contract, callback_data=f"contract_{contract}")]
            for contract in contracte
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("📄 Selectează un contract:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

# Callback pentru selecția contractului
async def contract_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contract_name = query.data.replace("contract_", "")
    keyboard = [
        [
            InlineKeyboardButton("✅ Da", callback_data=f"confirm_yes_{contract_name}"),
            InlineKeyboardButton("❌ Nu", callback_data="confirm_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        f"Ai selectat: *{contract_name}*\nVrei să continui?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Callback pentru confirmare
async def confirm_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_yes_"):
        contract_name = data.replace("confirm_yes_", "")
        await query.message.reply_text(f"✅ Contractul *{contract_name}* va fi trimis.", parse_mode="Markdown")
        # Aici poți adăuga logica pentru a trimite contractul pe email etc.
    elif data == "confirm_no":
        await query.message.reply_text("❌ Anulat.")

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comenzi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))

    # Callbacks
    app.add_handler(CallbackQueryHandler(contract_select, pattern="^contract_"))
    app.add_handler(CallbackQueryHandler(confirm_select, pattern="^confirm_"))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
