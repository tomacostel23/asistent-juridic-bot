import os
import json
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 Citim credențialele Google din variabilele de mediu
creds_dict = {
    "type": os.environ.get("GOOGLE_TYPE"),
    "project_id": os.environ.get("GOOGLE_PROJECT_ID"),
    "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
    "auth_uri": os.environ.get("GOOGLE_AUTH_URI"),
    "token_uri": os.environ.get("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("GOOGLE_AUTH_PROVIDER_CERT"),
    "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": os.environ.get("GOOGLE_UNIVERSE_DOMAIN")
}

print("🔍 DEBUG: creds_dict =")
print(creds_dict)

# 🔗 Conectare Google Sheets
gc = gspread.service_account_from_dict(creds_dict)

# 🆔 ID-ul Google Sheet (schimbă-l cu ID-ul real al fișierului tău!)
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")  # ex: '1AbCdEfGhIjKlMnOpQrStUvWxYz'

# 🔑 Citim token-ul Telegram din env
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# 🤖 Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Sunt Asistentul Juridic 🤖")

# 🤖 Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comanda /trimite_contract a fost primită ✅")

# 🤖 Comanda /lista_contracte
async def lista_contracte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Deschidem sheet-ul după ID
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sh.sheet1  # presupunem că e primul sheet (poți schimba dacă ai mai multe foi)

        # Citim toată coloana B (Denumire)
        denumiri = worksheet.col_values(2)  # coloana B = 2

        if not denumiri:
            await update.message.reply_text("Nu am găsit niciun contract în listă ❗")
        else:
            # Ignorăm eventual header-ul (dacă primul rând e "Denumire")
            if denumiri[0].strip().lower() == 'denumire':
                denumiri = denumiri[1:]

            mesaj = "📄 Lista contractelor:\n" + "\n".join(f"- {den}" for den in denumiri)
            await update.message.reply_text(mesaj)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Eroare la citirea Google Sheet: {e}")

# 🔄 Pornim aplicația
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trimite_contract", trimite_contract))
    app.add_handler(CommandHandler("lista_contracte", lista_contracte))

    print("🚀 Botul rulează...")
    app.run_polling()
