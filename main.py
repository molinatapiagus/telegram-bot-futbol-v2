import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no definido")

if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY no definido")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("⚽ Partidos de hoy", callback_data="today")]]
    await update.message.reply_text(
        "🤖 Bot de fútbol activo",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    r = requests.get("https://api.football-data.org/v4/matches", headers=HEADERS)
    if r.status_code != 200:
        await query.edit_message_text("Error consultando la API.")
        return

    matches = r.json().get("matches", [])[:5]
    if not matches:
        await query.edit_message_text("No hay partidos hoy.")
        return

    text = "⚽ Partidos de hoy:\n\n"
    for m in matches:
        text += f"{m['homeTeam']['name']} vs {m['awayTeam']['name']}\n"

    await query.edit_message_text(text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(today))
    app.run_polling()

if __name__ == "__main__":
    main()
