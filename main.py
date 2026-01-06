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

# ==============================
# CONFIGURACIÓN
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN or not FOOTBALL_API_KEY:
    raise RuntimeError("Faltan variables de entorno")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# ==============================
# TECLADO PRINCIPAL
# ==============================

def teclado_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# ==============================
# /start
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *Bot de análisis estadístico de fútbol*\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# ==============================
# OBTENER PARTIDOS DE HOY
# ==============================

def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": ""}
    response = requests.get(url, headers=HEADERS, params=params, timeout=20)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("response", [])

# ==============================
# BOTÓN ESTADÍSTICAS
# ==============================

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
        "📊 *Partidos encontrados*\n\n"
        "⚠️ Análisis avanzado en desarrollo.",
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# ==============================
# MAIN
# ==============================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="^stats$"))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
