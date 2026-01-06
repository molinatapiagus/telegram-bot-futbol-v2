import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================
# CONFIGURACIÓN
# ======================
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

# ======================
# TECLADO (SIEMPRE)
# ======================
def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# ======================
# /start
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Bot de fútbol activo\n\nPulsa el botón para analizar partidos de hoy.",
        reply_markup=keyboard()
    )

# ======================
# CALLBACK PRINCIPAL
# ======================
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = f"{API_BASE}/fixtures"
    params = {"date": "today"}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
    except Exception:
        await query.message.reply_text(
            "❌ Error consultando la API.",
            reply_markup=keyboard()
        )
        return

    fixtures = data.get("response", [])

    if not fixtures:
        await query.message.reply_text(
            "❌ No hay partidos disponibles hoy.\n\nVuelve más tarde.",
            reply_markup=keyboard()  # 🔴 AQUÍ ESTABA EL ERROR
        )
        return

    # Tomamos SOLO el primer partido (para no sobrecargar)
    match = fixtures[0]
    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    fixture_id = match["fixture"]["id"]

    stats_url = f"{API_BASE}/predictions"
    stats_params = {"fixture": fixture_id}

    stats_response = requests.get(stats_url, headers=HEADERS, params=stats_params).json()
    predictions = stats_response.get("response", [])

    if not predictions:
        await query.message.reply_text(
            f"📊 {home} vs {away}\n\nNo hay estadísticas suficientes.",
            reply_markup=keyboard()
        )
        return

    pred = predictions[0]["predictions"]

    over = pred["under_over"]
    btts = pred["both_teams_to_score"]

    mensaje = (
        f"📊 *Análisis del partido*\n\n"
        f"⚽ {home} vs {away}\n\n"
        f"📈 Over / Under 2.5: *{over}*\n"
        f"🔁 Ambos marcan: *{btts}*\n\n"
        f"✅ *Apuesta más probable:* "
    )

    if "Over" in over and "Yes" in btts:
        mensaje += "Over 2.5 + Ambos marcan"
    elif "Over" in over:
        mensaje += "Over 2.5"
    elif "Yes" in btts:
        mensaje += "Ambos marcan"
    else:
        mensaje += "No apostar (riesgo alto)"

    await query.message.reply_text(
        mensaje,
        reply_markup=keyboard(),
        parse_mode="Markdown"
    )

# ======================
# MAIN
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()

