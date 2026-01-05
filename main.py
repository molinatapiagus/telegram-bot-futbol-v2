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
BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no definido")

if not FOOTBALL_API_KEY:
    raise RuntimeError("FOOTBALL_API_KEY no definido")

API_URL = "https://v3.football.api-sports.io/fixtures"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}


# =====================
# COMANDOS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🤖 Bot de fútbol activo\n\nPulsa el botón para analizar partidos de hoy.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =====================
# CALLBACK
# =====================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        params = {"date": context.application.bot_data.get("today")}
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=15)
        data = response.json()

        if not data.get("response"):
            await query.edit_message_text(
                "❌ No hay partidos disponibles hoy.\n\nVuelve más tarde."
            )
            return

        # Ejemplo simple (hoy solo estructura base)
        await query.edit_message_text(
            "📊 Análisis disponible:\n\n"
            "✔ Over / Under\n"
            "✔ Ambos marcan\n\n"
            "⚠️ Análisis avanzado en progreso."
        )

    except Exception as e:
        await query.edit_message_text("❌ Error consultando la API")


# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="stats"))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()


if __name__ == "__main__":
    main()
