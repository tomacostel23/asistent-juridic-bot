import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from google.oauth2.service_account import Credentials

# Setăm logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Citim variabilele de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_PRIVATE_KEY_ID = os.getenv("GOOGLE_PRIVATE_KEY_ID")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY")
GOOGLE_CLIENT_EMAIL = os.getenv("GOOGLE_CLIENT_EMAIL")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Debug pentru a verifica variabilele
print(f"DEBUG: TELEGRAM_TOKEN = {repr(TELEGRAM_TOKEN)}")
print(f"DEBUG: GOOGLE_PRIVATE_KEY = {repr(GOOGLE_PRIVATE_KEY)}")

# Construim dictionarul de credentials
creds_dict = {
    "type": "service_account",
    "project_id": GOOGLE_PROJECT_ID,
    "private_key_id": GOOGLE_PRIVATE_KEY_ID,
    "private_key": GOOGLE_PRIVATE_KEY,
    "client_email": GOOGLE_CLIENT_EMAIL,
    "client_id": GOOGLE_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{GOOGLE_CLIENT_EMAIL.replace('@', '%40')}"
}

# Procesăm cheia privată pentru a înlocui \\n cu newline-uri reale
try:
    creds_dict["private_key"] = creds_dict["private_key"].encode().decode('unicode_escape')
except Exception as e:
    logger.error(f"Eroare la procesarea cheii private: {e}")

print(f"DEBUG: GOOGLE_PRIVATE_KEY (processed) = {repr(creds_dict['private_key'])}")

# Inițializăm clientul Google Sheets
gc = None
try:
    credentials = Credentials.from_service_account_info(creds_dict)
    gc = gspread.authorize(credentials)
except Exception as e:
    logger.error(f"Eroare la conectarea la Google Sheets: {e}")

# Conversație pentru trimiterea contractelor
CHOOSING_CONTRACT, CONFIRMING_SEND = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Folosește comanda /trimite_contract pentru a începe.")

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return ConversationHandler.END

    try:
        sh = gc.open("Lista_contracte")
        worksheet = sh.sheet1
        contracts = worksheet.col_values(2)  # Coloana B
        if not contracts:
            await update.message.reply_text("Nu am găsit niciun contract.")
            return ConversationHandler.END

        context.user_data["contracts"] = contracts[1:]  # Excludem headerul
        keyboard = [[contract] for contract in context.user_data["contracts"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            "📄 Selectează un contract din listă:",
            reply_markup=reply_markup
        )
        return CHOOSING_CONTRACT

    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")
        return ConversationHandler.END

async def contract_ales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contract = update.message.text
    context.user_data["contract_selectat"] = contract

    await update.message.reply_text(
        f"Ai selectat contractul:\n\n📄 {contract}\n\nEști sigur că vrei să continui? (da/nu)"
    )
    return CONFIRMING_SEND

async def confirmare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raspuns = update.message.text.lower()
    contract = context.user_data.get("contract_selectat")

    if raspuns == "da":
        await update.message.reply_text(f"✅ Contractul '{contract}' va fi trimis!")
        # Aici adaugi logica de trimitere efectivă a contractului
    else:
        await update.message.reply_text("❌ Trimiterea a fost anulată.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Am anulat operațiunea.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("trimite_contract", trimite_contract)],
        states={
            CHOOSING_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contract_ales)],
            CONFIRMING_SEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmare)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
