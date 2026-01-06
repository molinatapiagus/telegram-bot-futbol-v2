import os
import json
import requests
import asyncio
from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

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
# TELEGRAM APP
# =========================

telegram_app = Application.builder().token(BOT_TOKEN).build()

# =========================
# FLASK APP
# =========================

flask_app = Flask(__name__)

# =========================
# TECLADO
# =========================

def teclado_principal():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]]
    )

# =========================
# COMANDOS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *Bot de análisis estadístico de fútbol*\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        parse_mode="Markdown",
        reply_markup=teclado_principal(),
    )

# =========================
# API FOOTBALL
# =========================

def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": request_date()}
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    data = r.json()
    return data.get("response", [])

def request_date():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")

# =========================
# CALLBACK
# =========================

async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.edit_message_text(
            "❌ Hoy no hay partidos disponibles.\nInténtalo más tarde.",
            reply_markup=teclado_principal(),
        )
        return

    mensaje = "📊 *Partidos disponibles hoy:*\n\n"

    for p in partidos[:5]:
        local = p["teams"]["home"]["name"]
        visita = p["teams"]["away"]["name"]
        mensaje += f"• {local} vs {visita}\n"

    mensaje += "\n🔎 *Próximamente:* análisis Over/Under y Ambos Marcan."

    await query.edit_message_text(
        mensaje,
        parse_mode="Markdown",
        reply_markup=teclado_principal(),
    )

# =========================
# REGISTRO HANDLERS
# =========================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="^stats$"))

# =========================
# WEBHOOK ENDPOINT
# =========================

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

# =========================
# INICIO
# =========================

async def iniciar():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

asyncio.run(iniciar())

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

