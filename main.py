import os
import json
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Citim variabilele din ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
SHEET_ID = os.getenv("SHEET_ID")  # trebuie sa ai și acest env pentru ID-ul foii Google

# Debug info
logger.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logger.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:40]}")

# Prelucrare JSON credentials
try:
    creds_json_raw = GOOGLE_CREDS_JSON
    logger.info(f"DEBUG: RAW creds starts with: {creds_json_raw[:40]}")
    creds_json_fixed = creds_json_raw.replace('\\n', '\n')
    logger.info(f"DEBUG: FIXED creds starts with: {creds_json_fixed[:40]}")
    creds_dict = json.loads(creds_json_fixed)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    logger.info("✅ Conectat la Google Sheets.")
except Exception as e:
    logger.error(f"❌ Eroare la conectarea la Google Sheets: {e}")
    sheet = None

# Variabilă globală pentru a memora selecția curentă
user_selection = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Trimite comanda /trimite_contract ca să începem.")

async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheet is None:
        await update.message.reply_text("❌ Nu mă pot conecta la Google Sheets.")
        return

    try:
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range="A2:Z"  # presupunem că ai date în coloanele A–Z (ajustăm după nevoie)
        ).execute()
        values = result.get('values', [])

        if not values:
            await update.message.reply_text("❗️ Nu am găsit niciun contract în lista din Google Sheets.")
            return

        contracte = []
        for row in values:
            if len(row) >= 2:  # coloana 2 = denumire
                contracte.append(row[1])

        # Salvăm în context pentru utilizator
        user_selection[update.effective_user.id] = contracte

        # Construim mesajul
        mesaj = "📄 Lista contracte:\nSelectează unul dintre următoarele:\n\n"
        for idx, denumire in enumerate(contracte, 1):
            mesaj += f"{idx}. {denumire}\n"

        await update.message.reply_text(mesaj)

    except Exception as e:
        logger.error(f"❌ Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ A apărut o eroare la citirea contractelor.")

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_selection:
        await update.message.reply_text("ℹ️ Te rog să folosești mai întâi comanda /trimite_contract.")
        return

    text = update.message.text.strip()
    try:
        index = int(text) - 1
        contracts = user_selection[user_id]

        if index < 0 or index >= len(contracts):
            await update.message.reply_text("❗️ Număr invalid. Te rog să alegi un număr valid din listă.")
            return

        selected_contract = contracts[index]
        context.user_data['selected_contract'] = selected_contract

        # Cerem confirmare
        await update.message.reply_text(
            f"Ai selectat: {selected_contract}\n✅ Ești sigur? (da/nu)"
        )
    except ValueError:
        await update.message.reply_text("❗️ Te rog să trimiți un număr valid corespunzător contractului dorit.")

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = update.message.text.strip().lower()
    selected_contract = context.user_data.get('selected_contract')

    if not selected_contract:
        await update.message.reply_text("ℹ️ Nu ai selectat încă un contract. Folosește mai întâi comanda /trimite_contract.")
        return

    if response == "da":
        await update.message.reply_text(f"✅ Contractul '{selected_contract}' va fi trimis acum.")
        # TODO: aici adaugi logica pentru completarea și trimiterea contractului
    elif response == "nu":
        await update.message.reply_text("❌ Am anulat selecția. Poți selecta alt contract din listă.")
    else:
        await update.message.reply_text("❗️ Te rog să răspunzi cu 'da' sau 'nu'.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(MessageHandler(filters.Regex(r"^\d+$"), handle_selection))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^(da|nu)$"), handle_confirmation))

    logger.info("🚀 Bot-ul rulează...")
    app.run_polling()
