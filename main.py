import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔑 Citește variabilele de mediu
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
SHEET_NAME = os.environ.get('SHEET_NAME')
GOOGLE_CREDS_JSON = os.environ.get('GOOGLE_CREDS_JSON')

# 🗂️ Setări Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 👥 Etapele conversației
SELECT_CONTRACT, ASK_NAME, ASK_EMAIL = range(3)

# 📄 Inițializează Google Sheets client
def init_gsheet():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

# ▶️ Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Trimite comanda /trimite_contract ca să începem procesul.")

# 📨 Trimite contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = init_gsheet()
        data = sheet.get_all_values()

        # Citește contractele (din rândurile după header)
        contracte = [row[1] for row in data[1:]]  # Coloana 2 = numele contractului
        context.user_data['contracte'] = contracte

        # Generează lista frumos numerotată
        msg = "Alege contractul dorit:\n"
        for idx, contract in enumerate(contracte, 1):
            msg += f"{idx}. {contract}\n"

        await update.message.reply_text(msg)
        return SELECT_CONTRACT

    except Exception as e:
        await update.message.reply_text(f"Eroare la citirea contractelor: {str(e)}")
        return ConversationHandler.END

# 🟢 Selectează contractul
async def select_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text.strip()) - 1
        context.user_data['contract_idx'] = idx
        contracte = context.user_data['contracte']
        await update.message.reply_text(
            f"Ai ales: {contracte[idx]}\nCum se numește persoana/instituția către care trimiți?")
        return ASK_NAME
    except (ValueError, IndexError):
        await update.message.reply_text("Te rog alege un număr valid din listă.")
        return SELECT_CONTRACT

# 👤 Întreabă numele
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nume = update.message.text.strip()
    context.user_data['nume_destinatar'] = nume
    await update.message.reply_text(f"Perfect. Care este emailul acestei persoane?")
    return ASK_EMAIL

# ✅ Finalizare (pentru test)
async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    nume = context.user_data['nume_destinatar']
    idx = context.user_data['contract_idx']
    contract = context.user_data['contracte'][idx]

    await update.message.reply_text(
        f"✅ Super! Am primit datele:\n"
        f"- Contract: {contract}\n"
        f"- Destinatar: {nume}\n"
        f"- Email: {email}\n\n"
        f"(În pasul următor vom implementa trimiterea emailului 😊)"
    )

    return ConversationHandler.END

# ▶️ Setup bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversație cu etapele definite
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("trimite_contract", trimite_contract)],
        states={
            SELECT_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_contract)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, finalize)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
