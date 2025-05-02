import logging
import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

# Citim din ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Debug ENV vars
logging.info(f"DEBUG: TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
logging.info(f"DEBUG: GOOGLE_CREDS_JSON starts with: {GOOGLE_CREDS_JSON[:50]}")

# Salvăm într-un fișier pentru verificare manuală
with open("debug_creds.json", "w") as f:
    f.write(GOOGLE_CREDS_JSON)
logging.info("✅ Am salvat GOOGLE_CREDS_JSON în debug_creds.json pentru verificare manuală.")

# 1️⃣ Testăm direct JSON-ul primit (fără replace)
try:
    creds_info_direct = json.loads(GOOGLE_CREDS_JSON)
    logging.info("✅ JSON loaded cu SUCCES direct (fără replace())")
except json.JSONDecodeError as e:
    logging.error(f"❌ Eroare la JSON direct: {e}")

# 2️⃣ Testăm cu replace()
try:
    GOOGLE_CREDS_JSON_FIXED = GOOGLE_CREDS_JSON.replace("\\n", "\n")
    creds_info_fixed = json.loads(GOOGLE_CREDS_JSON_FIXED)
    logging.info("✅ JSON loaded cu SUCCES după replace()")
except json.JSONDecodeError as e:
    logging.error(f"❌ Eroare la JSON cu replace(): {e}")

# Comanda /start simplă
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salut! Bot-ul funcționează.")

# Pornim botul
if TELEGRAM_TOKEN:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logging.info("🚀 Bot-ul rulează...")
    app.run_polling()
else:
    logging.error("❌ TELEGRAM_TOKEN lipsește!")
