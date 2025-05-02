import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from google.oauth2.service_account import Credentials
import gspread

# Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Citire token și credențiale din ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:40]}")

# Conectare la Google Sheets
gc = None
try:
    # Fixăm eventualele probleme cu newline-urile din JSON
    raw_creds = GOOGLE_CREDS_JSON
    logger.info(f"DEBUG: RAW creds starts with: {raw_creds[:40]}")
    fixed_creds = raw_creds.replace("\\n", "\n")
    logger.info(f"DEBUG: FIXED creds starts with: {fixed_creds[:40]}")

    creds_dict = json.loads(fixed_creds)
    creds = Credentials.from_service_account_info(creds_dict, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    gc = gspread.authorize(creds)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Trimite comanda /trimite_contract pentru a începe.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contracte = [
        "Contract Agentie imobiliara - comision 0.6%",
        "Contract Agentie imobiliara - comision 0.5%",
        "Contract colaborator"
    ]
    reply_keyboard = [[contract] for contract in contracte]
    await update.message.reply_text(
        "📄 Lista contracte:\nSelectează unul dintre următoarele:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Handler când selectezi un contract
async def handle_contract_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_contract = update.message.text
    context.user_data["selected_contract"] = selected_contract

    reply_keyboard = [["Da", "Nu"]]
    await update.message.reply_text(
        f"Ai selectat: *{selected_contract}*\n\n✅ Confirmi selecția?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )

# Handler pentru confirmare (da/nu)
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raspuns = update.message.text.lower()
    selected_contract = context.user_data.get("selected_contract", "Nespecificat")

    if raspuns == "da":
        await update.message.reply_text(f"✅ Contractul *{selected_contract}* va fi trimis.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Am anulat trimiterea contractului.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(MessageHandler(
        filters.Regex(r"^(Contract Agentie imobiliara - comision 0\.6%|Contract Agentie imobiliara - comision 0\.5%|Contract colaborator)$"),
        handle_contract_selection
    ))
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(da|nu)$"),  # <-- aici e fixul pentru case-insensitive
        handle_confirmation
    ))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

