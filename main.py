import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# CONFIGURACIÓN
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no definido")

if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY no definido")

HEADERS = {
    "X-Auth-Token": FOOTBALL_API_KEY
}

# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚽ Partidos de hoy", callback_data="today")]
    ]

    await update.message.reply_text(
        "🤖 Bot de fútbol activo.\nSelecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = "https://api.football-data.org/v4/matches?status=SCHEDULED"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        data = response.json()

        matches = data.get("matches", [])[:5]

        if not matches:
            await query.edit_message_text("⚠️ No hay partidos programados hoy.")
            return

        text = "⚽ *Partidos de hoy:*\n\n"

        for m in matches:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            time = m["utcDate"][11:16]
            text += f"{home} vs {away} — {time} UTC\n"

        await query.edit_message_text(text, parse_mode="Markdown")

    except Exception as e:
        await query.edit_message_text("❌ Error al consultar la API de fútbol.")


# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(today, pattern="today"))

    # ⚠️ CLAVE PARA RENDER (BUG FIX)
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

