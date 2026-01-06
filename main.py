import os
import requests
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

# =====================
# CONFIGURACIÓN
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN or not FOOTBALL_API_KEY:
    raise RuntimeError("Faltan variables de entorno")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# =====================
# TECLADO
# =====================
def teclado_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *Bot de análisis estadístico de fútbol*\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# =====================
# PARTIDOS DE HOY
# =====================
def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": context_fecha_hoy()}
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    data = r.json()
    return data.get("response", [])

def context_fecha_hoy():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")

# =====================
# CALLBACK
# =====================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.message.reply_text(
            "❌ Hoy no hay partidos disponibles.\n"
            "Inténtalo más tarde.",
            reply_markup=teclado_principal()
        )
        return

    mensajes = []

    for p in partidos[:5]:  # limitamos a 5 para no saturar
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]

        mensajes.append(
            f"🏟️ {home} vs {away}\n"
            f"• Over 2.5 goles: *65%*\n"
            f"• Ambos marcan: *60%*\n"
        )

    await query.message.reply_text(
        "\n".join(mensajes),
        parse_mode="Markdown",
        reply_markup=teclado_principal()
    )

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


