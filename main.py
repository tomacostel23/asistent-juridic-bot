import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import gspread
from dotenv import load_dotenv

# Configurare logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Încărcare variabile de mediu
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME")

# Configurare gspread
creds_dict = {
    "type": os.environ.get("GOOGLE_TYPE"),
    "project_id": os.environ.get("GOOGLE_PROJECT_ID"),
    "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
    "auth_uri": os.environ.get("GOOGLE_AUTH_URI"),
    "token_uri": os.environ.get("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_X509_CERT_URL"),
}

gc = gspread.service_account_from_dict(creds_dict)

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = gc.open(GOOGLE_SHEET_NAME).sheet1
        contracte = sheet.col_values(2)[1:]  # Col B, ignorăm headerul

        buttons = [
            [InlineKeyboardButton(text=contract, callback_data=f"select_{contract}")]
            for contract in contracte
        ]

        await update.message.reply_text(
            "📄 Lista contracte:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("select_"):
        contract_name = query.data.replace("select_", "")

        buttons = [
            [
                InlineKeyboardButton("✅ Da", callback_data=f"confirm_yes_{contract_name}"),
                InlineKeyboardButton("❌ Nu", callback_data="confirm_no")
            ]
        ]

        await query.message.reply_text(
            f"Ai selectat: *{contract_name}*\n\nVrei să continui cu acest contract?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data.startswith("confirm_yes_"):
        contract_name = query.data.replace("confirm_yes_", "")
        await query.message.reply_text(f"✅ Contractul *{contract_name}* a fost confirmat și va fi procesat. 📄", parse_mode="Markdown")
        # Aici adaugi logica pentru a trimite contractul efectiv.

    elif query.data == "confirm_no":
        await query.message.reply_text("🔄 Am anulat selecția. Poți alege din nou un contract cu comanda /trimite_contract.")


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("trimite_contract", trimite_contract))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Bot-ul rulează...")
    application.run_polling()

if __name__ == '__main__':
    main()

