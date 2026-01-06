import os
import json
import requests
from datetime import datetime
from flask import Flask, request

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# ============ HANDLERS ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Bienvenido. Usa /juegos para ver partidos."
    await update.message.reply_text(text)

async def juegos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"

    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()

    if not data.get("response"):
        await update.message.reply_text("Hoy no hay partidos disponibles. Inténtalo más tarde.")
        return

    mensaje = "Partidos de hoy:\n\n"
    for match in data["response"]:
        league = match["league"]["name"]
        teams = match["teams"]["home"]["name"] + " vs " + match["teams"]["away"]["name"]
        hora = match["fixture"]["date"][11:16]
        mensaje += f"{league}: {teams} - {hora}\n"

    await update.message.reply_text(mensaje)

# Registrar comandos
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("juegos", juegos))

# ============ FLASK ROUTES =============

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot activo", 200

# ============ RUN =============

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TOKEN}"
    )

