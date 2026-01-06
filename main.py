import os
import requests
import asyncio
from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# =====================
# CONFIGURACIÓN
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not FOOTBALL_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Faltan variables de entorno")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# =====================
# FLASK
# =====================
flask_app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# =====================
# BOTONES
# =====================
def teclado_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# =====================
# COMANDOS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Bot de análisis estadístico de fútbol\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        reply_markup=teclado_principal()
    )

# =====================
# CALLBACK
# =====================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Aquí luego conectamos Over/Under y Ambos Marcan
    await query.message.reply_text(
        "❌ Hoy no hay partidos disponibles.\n"
        "Inténtalo más tarde.",
        reply_markup=teclado_principal()
    )

# =====================
# WEBHOOK ENDPOINT
# =====================
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

# =====================
# MAIN
# =====================
def main():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="stats"))

    async def setup():
        await telegram_app.bot.set_webhook(WEBHOOK_URL)

    asyncio.run(setup())

    flask_app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()

