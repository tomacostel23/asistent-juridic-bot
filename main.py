import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread

# Logging basic pentru debug
logging.basicConfig(level=logging.INFO)

# Pregătim credențialele din variabilele de mediu
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

# Debug la cheie ca să vezi cum arată înainte și după replace
print("\nDEBUG: RAW PRIVATE_KEY (from ENV):")
print(os.environ.get("GOOGLE_PRIVATE_KEY"))

print("\nDEBUG: PROCESSED PRIVATE_KEY (after replace):")
print(creds_dict["private_key"])

# Inițializăm gspread
try:
    gc = gspread.service_account_from_dict(creds_dict)
    logging.info("✅ Conectat la Google Sheets!")
except Exception as e:
    logging.error(f"Eroare la conectarea la Google Sheets: {e}")

# Funcția comandă /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comanda /trimite_contract a fost primită ✅")

    try:
        # Accesăm sheet-ul
        sh = gc.open("Lista_contracte")
        worksheet = sh.sheet1  # sau folosește sheet-ul dorit
        
        # Citim coloana B (care are titlul 'Denumire')
        denumiri = worksheet.col_values(2)  # coloana B este index 2
        denumiri_text = "\n".join(denumiri)
        
        await update.message.reply_text(f"📄 Lista contracte:\n{denumiri_text}")

    except Exception as e:
        logging.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text("❌ Eroare la citirea contractelor.")

# Pornim bot-ul
if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("trimite_contract", trimite_contract))

    logging.info("🚀 Bot-ul rulează...")
    app.run_polling()
