import os
import json
import logging

import gspread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Configurare logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Încarcă variabilele din ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}...")

# Setăm Google Sheets API
gc = None
try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    gc = gspread.service_account_from_dict(creds_dict)
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")

# Stările pentru ConversationHandler
SELECTING_CONTRACT, CONFIRMING_SELECTION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salut! Folosește comanda /trimite_contract pentru a începe."
    )

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if gc is None:
        await update.message.reply_text("❌ Eroare: nu mă pot conecta la Google Sheets.")
        return ConversationHandler.END

    try:
        sh = gc.open("Contracte")
        worksheet = sh.sheet1
        contracts = worksheet.col_values(1)
        if not contracts:
            await update.message.reply_text("📂 Nu există contracte disponibile.")
            return ConversationHandler.END

        buttons = [[KeyboardButton(c)] for c in contracts]
        reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            "📄 Alege un contract din listă:", reply_markup=reply_markup
        )
        return SELECTING_CONTRACT
    except Exception as e:
        logger.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")
        return ConversationHandler.END

async def confirm_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contract_selected = update.message.text
    context.user_data["contract"] = contract_selected

    buttons = [[KeyboardButton("Da")], [KeyboardButton("Nu")]]
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Ai selectat: *{contract_selected}*\nVrei să continui?",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CONFIRMING_SELECTION

async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = update.message.text.lower()
    contract_selected = context.user_data.get("contract", "necunoscut")

    if response == "da":
        await update.message.reply_text(f"📤 Trimit contractul: *{contract_selected}*", parse_mode="Markdown")
        # Aici vei adăuga logica efectivă pentru trimiterea contractului
    else:
        await update.message.reply_text("❌ Procesul a fost anulat.")

    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("trimite_contract", trimite_contract)],
        states={
            SELECTING_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_contract)],
            CONFIRMING_SELECTION: [MessageHandler(filters.Regex("^(Da|Nu)$"), finalize)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()

if __name__ == "__main__":
    main()
