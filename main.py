import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =====================
# CONFIGURACIÓN
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no definido")

if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY no definido")

HEADERS = {
    "X-Auth-Token": FOOTBALL_API_KEY
}

# =====================
# COMANDOS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚽ Partidos de hoy", callback_data="today")]
    ]
    await update.message.reply_text(
        "🤖 Bot de fútbol activo",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# CALLBACKS
# =====================
async def partidos_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = "https://api.football-data.org/v4/matches?dateFrom=today&dateTo=today"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        await query.edit_message_text(
            "❌ Error consultando la API"
        )
        return

    data = response.json()
    matches = data.get("matches", [])

    if not matches:
        texto = "📭 No hay partidos hoy."
    else:
        texto = "⚽ Partidos de hoy:\n\n"
        for m in matches[:10]:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            texto += f"{home} vs {away}\n"

    # 🔁 VOLVER A MOSTRAR EL BOTÓN
    keyboard = [
        [InlineKeyboardButton("⚽ Partidos de hoy", callback_data="today")]
    ]

    await query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(partidos_hoy, pattern="today"))

    print("Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
