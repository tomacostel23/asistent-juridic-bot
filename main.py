import os
import logging
from dotenv import load_dotenv
import gspread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Configurare logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Încarcă variabilele de mediu
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Debug - verificăm dacă token-ul și cheia sunt corecte
logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")

creds_dict = {
    "type": "service_account",
    "project_id": os.getenv('GOOGLE_PROJECT_ID'),
    "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
}

logger.info(f"DEBUG: GOOGLE_PRIVATE_KEY starts with: {creds_dict['private_key'][:30]}...")

# Inițializează Google Sheets
try:
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open('Lista_contracte')
    worksheet = sh.sheet1
    logger.info("✅ Conectat la Google Sheets!")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    gc = None  # În caz de eroare, setăm gc ca None

# Stări pentru conversație
SELECT_CONTRACT, CONFIRMATION = range(2)

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Trimite comanda /trimite_contract pentru a începe.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return ConversationHandler.END

    try:
        contracte = worksheet.col_values(2)[1:]  # Ignorăm headerul
        context.user_data['contracte'] = contracte

        if not contracte:
            await update.message.reply_text("⚠️ Nu există contracte disponibile.")
            return ConversationHandler.END

        # Trimitem lista de contracte
        lista = "\n".join([f"{i+1}. {nume}" for i, nume in enumerate(contracte)])
        await update.message.reply_text(
            f"📄 Lista contracte:\n{lista}\n\nScrie numărul contractului pe care îl vrei:"
        )
        return SELECT_CONTRACT
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")
        return ConversationHandler.END

# Selectarea contractului
async def select_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Te rog să scrii un număr valid.")
        return SELECT_CONTRACT

    index = int(text) - 1
    contracte = context.user_data.get('contracte', [])

    if index < 0 or index >= len(contracte):
        await update.message.reply_text("⚠️ Număr invalid. Încearcă din nou.")
        return SELECT_CONTRACT

    context.user_data['selected_contract'] = contracte[index]
    reply_keyboard = [['Da', 'Nu']]
    await update.message.reply_text(
        f"Ai selectat: *{contracte[index]}*.\nEști sigur?",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRMATION

# Confirmarea finală
async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raspuns = update.message.text.strip().lower()
    contract = context.user_data.get('selected_contract')

    if raspuns == 'da':
        await update.message.reply_text(f"✅ Contractul *{contract}* a fost trimis!", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Comanda a fost anulată.")
    return ConversationHandler.END

# Funcția main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('trimite_contract', trimite_contract)],
        states={
            SELECT_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_contract)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
