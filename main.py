import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
import gspread

# Configurare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variabile pentru stările conversației
SELECT_CONTRACT, CONFIRM_CONTRACT = range(2)

# Setări Google Sheets
SERVICE_ACCOUNT_INFO = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN"),
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Conectare Google Sheets
try:
    gc = gspread.service_account_from_dict(SERVICE_ACCOUNT_INFO)
    sh = gc.open("Lista_contracte")
    worksheet = sh.sheet1
except Exception as e:
    logger.error(f"Eroare la conectarea la Google Sheets: {e}")
    gc = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Folosește comanda /trimite_contract pentru a începe.")


async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("❌ Nu pot accesa Google Sheets momentan.")
        return ConversationHandler.END

    try:
        contracts = worksheet.col_values(2)[1:]  # Coloana B fără header
        if not contracts:
            await update.message.reply_text("📄 Nu am găsit niciun contract disponibil.")
            return ConversationHandler.END

        contract_list = "\n".join(contracts)
        reply_keyboard = [[contract] for contract in contracts]

        await update.message.reply_text(
            f"📄 Lista contracte:\n{contract_list}\n\nAlege un contract din lista de mai jos 👇",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return SELECT_CONTRACT

    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")
        return ConversationHandler.END


async def select_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_contract = update.message.text
    context.user_data["selected_contract"] = selected_contract

    reply_keyboard = [["Da", "Nu"]]
    await update.message.reply_text(
        f"✅ Ai selectat:\n<b>{selected_contract}</b>\n\nVrei să continui?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="HTML",
    )
    return CONFIRM_CONTRACT


async def confirm_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text.lower()
    selected_contract = context.user_data.get("selected_contract")

    if confirmation == "da":
        await update.message.reply_text(
            f"🚀 Contractul <b>{selected_contract}</b> va fi trimis acum.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        # Aici poți adăuga logica de trimitere a contractului (de ex. pe email)
    else:
        await update.message.reply_text(
            "❌ Ai anulat trimiterea contractului.", reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Anulat. Dacă vrei să reîncepi, folosește comanda /trimite_contract.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("trimite_contract", trimite_contract)],
        states={
            SELECT_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_contract)],
            CONFIRM_CONTRACT: [MessageHandler(filters.Regex("^(Da|Nu)$"), confirm_contract)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

