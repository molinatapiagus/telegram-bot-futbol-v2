import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ======================
# CONFIGURACIÓN
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no definido")

if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY no definido")

HEADERS = {
    "X-Auth-Token": FOOTBALL_API_KEY
}

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚽ Partidos de hoy", callback_data="today")]
    ]
    await update.message.reply_text(
        "🤖 Bot de fútbol activo",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = "https://api.football-data.org/v4/matches?dateFrom=today&dateTo=today"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        await query.edit_message_text("❌ Error consultando la API")
        return

    data = r.json()
    matches = data.get("matches", [])

    if not matches:
        await query.edit_message_text("📭 No hay partidos hoy")
        return

    text = "⚽ Partidos de hoy:\n\n"
    for m in matches[:5]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        text += f"{home} vs {away}\n"

    await query.edit_message_text(text)

# ======================
# MAIN
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(today, pattern="today"))

    app.run_polling()

if __name__ == "__main__":
    main()

