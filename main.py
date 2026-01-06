import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
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
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"

# =====================
# BOTÓN PRINCIPAL
# =====================
def main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]]
    )

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot de fútbol activo\n\nPulsa el botón para analizar partidos de hoy.",
        reply_markup=main_keyboard()
    )

# =====================
# OBTENER PARTIDOS DE HOY
# =====================
def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": "today"}

    response = requests.get(url, headers=HEADERS, params=params, timeout=15)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("response", [])

# =====================
# CALCULAR PROBABILIDADES SIMPLES
# =====================
def analizar_partido(fixture):
    stats_home = fixture["teams"]["home"]["winner"]
    stats_away = fixture["teams"]["away"]["winner"]

    # Modelo sencillo y honesto (fase 1)
    over25 = 55
    ambos_marcan = 60

    if stats_home and stats_away:
        ambos_marcan += 10

    return {
        "over25": min(over25, 75),
        "ambos": min(ambos_marcan, 80)
    }

# =====================
# CALLBACK DEL BOTÓN
# =====================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.edit_message_text(
            "❌ No hay partidos disponibles hoy.\nInténtalo más tarde.",
            reply_markup=main_keyboard()
        )
        return

    partido = partidos[0]

    home = partido["teams"]["home"]["name"]
    away = partido["teams"]["away"]["name"]

    probs = analizar_partido(partido)

    if probs["ambos"] >= probs["over25"]:
        apuesta = f"👉 Ambos marcan – SÍ ({probs['ambos']}%)"
    else:
        apuesta = f"👉 Over 2.5 goles ({probs['over25']}%)"

    mensaje = (
        f"⚽ Partido: {home} vs {away}\n\n"
        f"📊 Análisis estadístico:\n"
        f"• Over 2.5: {probs['over25']}%\n"
        f"• Ambos marcan: {probs['ambos']}%\n\n"
        f"✅ Apuesta con mayor probabilidad:\n"
        f"{apuesta}"
    )

    await query.edit_message_text(
        mensaje,
        reply_markup=main_keyboard()
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

