import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# 🔧 Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔄 Încarcă variabilele din .env
load_dotenv()

# ✅ Citim TOKEN & CREDENȚIALE
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_PRIVATE_KEY starts with: {GOOGLE_PRIVATE_KEY[:30]}")

# 🔧 Construim dict-ul pentru gspread
creds_dict = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": GOOGLE_PRIVATE_KEY,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
}

# 🔄 Reparăm cheia privată
raw_private_key = creds_dict.get("private_key", "")
logger.info(f"DEBUG: RAW PRIVATE_KEY starts with: {raw_private_key[:30]}")
# Conversie inteligentă: decodează \n real
fixed_private_key = raw_private_key.encode().decode("unicode_escape")
creds_dict["private_key"] = fixed_private_key
logger.info(f"DEBUG: FIXED PRIVATE_KEY starts with: {creds_dict['private_key'][:30]}")

# ✅ Încearcă să te conectezi la Google Sheets
try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(credentials)
    logger.info("✅ Conectare la Google Sheets reușită!")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    gc = None

# ===== Handlere Telegram =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Trimite /trimite_contract ca să începem.")

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return

    # Exemplu: listăm niște contracte hardcodate
    lista_contracte = ["Contract A", "Contract B", "Contract C"]
    keyboard = [
        [InlineKeyboardButton(contract, callback_data=contract)]
        for contract in lista_contracte
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📄 Alege un contract:", reply_markup=reply_markup)

async def buton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contract_ales = query.data

    # Cerem confirmare tip da/nu
    keyboard = [
        [
            InlineKeyboardButton("✅ Da", callback_data=f"confirm_{contract_ales}"),
            InlineKeyboardButton("❌ Nu", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Ai ales: {contract_ales}\nEști sigur că vrei să continui?",
        reply_markup=reply_markup,
    )

async def confirmare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_"):
        contract_final = query.data.replace("confirm_", "")
        await query.edit_message_text(
            text=f"✅ Contractul **{contract_final}** va fi trimis în curând!"
        )
        # Aici poți adăuga logica de trimitere efectivă
    elif query.data == "cancel":
        await query.edit_message_text(text="❌ Operațiunea a fost anulată.")

# ===== Run bot =====

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CallbackQueryHandler(confirmare, pattern="^(confirm_|cancel)"))
    app.add_handler(CallbackQueryHandler(buton))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

