import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from flask import Flask, request

# =========================
# CONFIGURACIÓN
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not FOOTBALL_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Faltan variables de entorno")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# =========================
# FLASK APP
# =========================
flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

# =========================
# TECLADO
# =========================
def teclado_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *Bot de análisis estadístico de fútbol*\n\n"
        "Pulsa el botón para analizar partidos disponibles.",
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# =========================
# OBTENER PARTIDOS DE HOY
# =========================
def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": os.getenv("RENDER_DATE", "")}
    response = requests.get(url, headers=HEADERS, params=params, timeout=15)
    data = response.json()
    return data.get("response", [])

# =========================
# CALLBACK
# =========================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.message.reply_text(
            "❌ *Hoy no hay partidos disponibles.*\n"
            "Inténtalo más tarde.",
            reply_markup=teclado_principal(),
            parse_mode="Markdown"
        )
        return

    await query.message.reply_text(
        "📈 Partidos encontrados.\n"
        "El análisis avanzado se activará en el siguiente paso.",
        reply_markup=teclado_principal()
    )

# =========================
# WEBHOOK ENDPOINT
# =========================
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# =========================
# MAIN
# =========================
def main():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="stats"))

    telegram_app.bot.set_webhook(WEBHOOK_URL)

    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()

