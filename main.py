import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from google.oauth2.service_account import Credentials
import gspread
from dotenv import load_dotenv

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Încarcă variabilele de mediu
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GOOGLE_CREDS_JSON = os.getenv('GOOGLE_CREDS_JSON')

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Repară \\n în \n pentru cheia JSON
fixed_creds_json = GOOGLE_CREDS_JSON.replace('\\n', '\n')
logger.info(f"DEBUG: RAW creds starts with: {GOOGLE_CREDS_JSON[:50]}")
logger.info(f"DEBUG: FIXED creds starts with: {fixed_creds_json[:50]}")

# Initializează Google Sheets
gc = None
try:
    creds_dict = json.loads(fixed_creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ])
    gc = gspread.authorize(creds)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Sunt botul tău juridic. ✅ Folosește comanda /trimite_contract ca să începi.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if gc is None:
        await update.message.reply_text("❌ Nu mă pot conecta la Google Sheets.")
        return

    try:
        sheet = gc.open("Lista_Contracte").sheet1
        lista_contracte = sheet.col_values(1)[1:]  # presupunem că primul rând e header
        if not lista_contracte:
            await update.message.reply_text("Nu am găsit niciun contract în Google Sheets.")
            return

        reply_markup = ReplyKeyboardMarkup(
            [[contract] for contract in lista_contracte],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "📄 Alege un contract din lista de mai jos:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

# Confirmarea după selecție
async def handle_contract_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_contract = update.message.text
    context.user_data['selected_contract'] = selected_contract
    await update.message.reply_text(
        f"Ai selectat: {selected_contract}. ✅\nEști sigur că vrei să trimiți acest contract? (da/nu)"
    )

# Confirmare DA/NU
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    selected_contract = context.user_data.get('selected_contract')

    if not selected_contract:
        await update.message.reply_text("Nu ai selectat încă un contract. Folosește /trimite_contract.")
        return

    if text == 'da':
        await update.message.reply_text(f"✅ Contractul '{selected_contract}' a fost trimis cu succes!")
        # Aici poți adăuga logica reală pentru trimitere contract
    elif text == 'nu':
        await update.message.reply_text("🚫 Trimiterea contractului a fost anulată.")
    else:
        await update.message.reply_text("Te rog răspunde cu 'da' sau 'nu'.")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN lipsește. Verifică fișierul .env sau variabilele de mediu.")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('trimite_contract', trimite_contract))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_contract_selection
        ))
        app.add_handler(MessageHandler(
            filters.Regex('^(?i)(da|nu)$'),
            handle_confirmation
        ))

        logger.info("🚀 Bot-ul rulează...")
        app.run_polling()
