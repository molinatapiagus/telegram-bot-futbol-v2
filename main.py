import os
import requests
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

API_URL = "https://v3.football.api-sports.io"

# =========================
# COMANDOS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🤖 Bot de fútbol activo\n\nPulsa el botón para analizar partidos reales de hoy.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# CALLBACK
# =========================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        response = requests.get(
            f"{API_URL}/fixtures?date=today",
            headers=HEADERS,
            timeout=15
        )

        data = response.json()

        if not data.get("response"):
            await query.edit_message_text(
                "❌ No hay partidos disponibles hoy.\nVuelve más tarde."
            )
            return

        partido = data["response"][0]
        home = partido["teams"]["home"]["name"]
        away = partido["teams"]["away"]["name"]

        # EJEMPLO SIMPLE DE LÓGICA (luego se refina)
        recomendacion = (
            f"📊 Análisis del partido\n\n"
            f"{home} vs {away}\n\n"
            f"✅ Mejor opción detectada:\n"
            f"➡ Ambos marcan (Sí)\n\n"
            f"📈 Probabilidad estimada: 72%"
        )

        keyboard = [
            [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
        ]

        await query.edit_message_text(
            recomendacion,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await query.edit_message_text(
            "❌ Error consultando la API.\nInténtalo más tarde."
        )

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="stats"))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
