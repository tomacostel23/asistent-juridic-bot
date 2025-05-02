import logging
import os
import json
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Citire variabile de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_PRIVATE_KEY_ID = os.getenv("GOOGLE_PRIVATE_KEY_ID")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n")
GOOGLE_CLIENT_EMAIL = os.getenv("GOOGLE_CLIENT_EMAIL")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_X509_CERT_URL = os.getenv("GOOGLE_CLIENT_X509_CERT_URL")

# DEBUG: Verificăm valorile din ENV
print("DEBUG: TELEGRAM_TOKEN =", repr(TELEGRAM_TOKEN))
print("DEBUG: GOOGLE_PRIVATE_KEY =", repr(GOOGLE_PRIVATE_KEY))

# Setăm credentials pentru Google Sheets
creds_dict = {
    "type": "service_account",
    "project_id": GOOGLE_PROJECT_ID,
    "private_key_id": GOOGLE_PRIVATE_KEY_ID,
    "private_key": GOOGLE_PRIVATE_KEY,
    "client_email": GOOGLE_CLIENT_EMAIL,
    "client_id": GOOGLE_CLIENT_ID,
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": GOOGLE_CLIENT_X509_CERT_URL,
}

# Conectare Google Sheets
gc = None
try:
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("Lista_contracte")
    worksheet = sh.sheet1
    logging.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"Eroare la conectarea la Google Sheets: {e}")

# Dict pentru a ține minte selecția utilizatorilor
user_selection = {}

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Trimite comanda /trimite_contract pentru a începe.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if gc is None:
        await update.message.reply_text("❌ Eroare la citirea contractelor (Google Sheets nu este disponibil).")
        return

    try:
        contracte = worksheet.col_values(2)  # Coloana B = Denumire
        contracte = [c for c in contracte if c.strip()]  # Eliminăm golurile

        if not contracte:
            await update.message.reply_text("⚠️ Nu am găsit niciun contract.")
            return

        keyboard = [
            [InlineKeyboardButton(c, callback_data=f"select_{i}")]
            for i, c in enumerate(contracte)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📄 Lista contracte:\n" + "\n".join(contracte),
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

# Gestionăm apăsarea pe un buton (selecție contract)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("select_"):
        index = int(data.split("_")[1])
        try:
            contracte = worksheet.col_values(2)
            contracte = [c for c in contracte if c.strip()]
            contract = contracte[index]
            user_selection[query.from_user.id] = contract

            keyboard = [
                [
                    InlineKeyboardButton("✅ Da", callback_data="confirm_yes"),
                    InlineKeyboardButton("❌ Nu", callback_data="confirm_no")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"Ai selectat:\n\n📄 *{contract}*\n\nVrei să continui?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Eroare la procesarea selecției: {e}")
            await query.message.reply_text("❌ Eroare la procesarea selecției.")
    elif data == "confirm_yes":
        contract = user_selection.get(query.from_user.id)
        if contract:
            await query.message.reply_text(f"✅ Contractul *{contract}* a fost selectat pentru trimitere.", parse_mode="Markdown")
            # TODO: aici poți adăuga logica pentru trimiterea efectivă a contractului
        else:
            await query.message.reply_text("⚠️ Nu am găsit selecția ta.")
    elif data == "confirm_no":
        await query.message.reply_text("❌ Operațiunea a fost anulată.")

# Pornim botul
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("🚀 Bot-ul rulează...")
    app.run_polling()
