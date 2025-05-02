import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread

# Setăm logging-ul
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Citim variabilele de mediu
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME")

# Construim creds_dict cu debug detaliat
creds_dict = {
    "type": os.environ.get("GOOGLE_TYPE"),
    "project_id": os.environ.get("GOOGLE_PROJECT_ID"),
    "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GOOGLE_PRIVATE_KEY").encode('utf-8').decode('unicode_escape'),
    "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
    "auth_uri": os.environ.get("GOOGLE_AUTH_URI"),
    "token_uri": os.environ.get("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("GOOGLE_AUTH_PROVIDER_CERT"),
    "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": os.environ.get("GOOGLE_UNIVERSE_DOMAIN")
}

print("\nDEBUG: RAW PRIVATE_KEY (from ENV):")
print(os.environ.get("GOOGLE_PRIVATE_KEY"))

print("\nDEBUG: PROCESSED PRIVATE_KEY (after decode):")
print(creds_dict["private_key"])

# Conectăm la Google Sheets
gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open(SHEET_NAME)
worksheet = sh.sheet1

# Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Sunt Asistentul Juridic 🤖. Trimite comanda /trimite_contract ca să începem.")

# Comanda /trimite_contract
async def trimite_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comanda /trimite_contract a fost primită ✅\nCitesc contractele disponibile...")

    try:
        # Citim toate valorile din coloana B ("Denumire")
        denumiri = worksheet.col_values(2)  # Coloana 2 = B
        denumiri = [d for d in denumiri if d.strip() != ""]  # Eliminăm golurile

        if len(denumiri) == 0:
            await update.message.reply_text("Nu am găsit niciun contract în lista de pe Google Sheet.")
        else:
            lista_contracte = "\n".join([f"- {d}" for d in denumiri])
            await update.message.reply_text(f"📄 Contractele disponibile sunt:\n{lista_contracte}")

    except Exception as e:
        logging.error(f"Eroare la citirea contractelor: {e}")
        await update.message.reply_text(f"❌ Eroare la citirea contractelor: {e}")

# Setăm aplicația Telegram
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("trimite_contract", trimite_contract))

print("✅ Botul rulează și așteaptă comenzi...")
app.run_polling()

