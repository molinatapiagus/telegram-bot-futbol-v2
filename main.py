import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================
# CONFIGURACIÓN GENERAL
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN or not FOOTBALL_API_KEY:
    raise RuntimeError("Faltan variables de entorno")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# ======================
# TECLADO PRINCIPAL
# ======================
def teclado_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ])

# ======================
# COMANDO /start
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Bot de análisis estadístico de fútbol\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        reply_markup=teclado_principal()
    )

# ======================
# OBTENER PARTIDOS DEL DÍA
# ======================
def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": "today"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    data = r.json()
    return data.get("response", [])

# ======================
# OBTENER ESTADÍSTICAS DE EQUIPO
# ======================
def obtener_estadisticas_equipo(team_id, league_id, season):
    url = f"{API_BASE}/teams/statistics"
    params = {
        "team": team_id,
        "league": league_id,
        "season": season
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    return r.json().get("response", {})

# ======================
# CÁLCULO DE PROBABILIDADES REALES
# ======================
def calcular_probabilidades(fixture):
    league_id = fixture["league"]["id"]
    season = fixture["league"]["season"]

    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]

    home_stats = obtener_estadisticas_equipo(home_id, league_id, season)
    away_stats = obtener_estadisticas_equipo(away_id, league_id, season)

    # PROMEDIOS DE GOLES
    home_goals_for = float(home_stats["goals"]["for"]["average"]["total"])
    home_goals_against = float(home_stats["goals"]["against"]["average"]["total"])

    away_goals_for = float(away_stats["goals"]["for"]["average"]["total"])
    away_goals_against = float(away_stats["goals"]["against"]["average"]["total"])

    # ---- MÁS DE 2.5 GOLES ----
    media_total = (
        home_goals_for +
        home_goals_against +
        away_goals_for +
        away_goals_against
    ) / 2

    if media_total >= 3.0:
        mas_25 = 75
    elif media_total >= 2.5:
        mas_25 = 65
    else:
        mas_25 = 50

    # ---- AMBOS EQUIPOS MARCAN ----
    ambos_marcan = 0
    if home_goals_for >= 1 and away_goals_for >= 1:
        ambos_marcan += 30
    if home_goals_against >= 1 and away_goals_against >= 1:
        ambos_marcan += 30
    if home_goals_for >= 1.5 or away_goals_for >= 1.5:
        ambos_marcan += 10

    ambos_marcan = min(ambos_marcan, 80)

    return {
        "mas_25": mas_25,
        "ambos": ambos_marcan
    }

# ======================
# CALLBACK DEL BOTÓN
# ======================
async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.message.reply_text(
            "❌ Hoy no hay partidos disponibles.\nInténtalo más tarde.",
            reply_markup=teclado_principal()
        )
        return

    mejor_apuesta = None
    mejor_prob = 0
    mejor_partido = None

    for fixture in partidos:
        try:
            probs = calcular_probabilidades(fixture)
        except Exception:
            continue

        if probs["ambos"] > mejor_prob and probs["ambos"] >= 65:
            mejor_prob = probs["ambos"]
            mejor_apuesta = "Ambos equipos marcan – SÍ"
            mejor_partido = fixture

        if probs["mas_25"] > mejor_prob and probs["mas_25"] >= 65:
            mejor_prob = probs["mas_25"]
            mejor_apuesta = "Más de 2.5 goles"
            mejor_partido = fixture

    if not mejor_apuesta:
        await query.message.reply_text(
            "❌ Hoy no hay partidos con estadísticas suficientemente confiables.",
            reply_markup=teclado_principal()
        )
        return

    home = mejor_partido["teams"]["home"]["name"]
    away = mejor_partido["teams"]["away"]["name"]

    mensaje = (
        "⚽ ANÁLISIS ESTADÍSTICO DEL DÍA\n\n"
        f"🏟 Partido: {home} vs {away}\n\n"
        "📊 Apuesta con mayor probabilidad:\n"
        f"👉 {mejor_apuesta}\n\n"
        f"📈 Probabilidad estimada: {mejor_prob} %\n\n"
        "🧠 Basado en estadísticas reales.\n"
        "⚠️ Análisis informativo."
    )

    await query.message.reply_text(
        mensaje,
        reply_markup=teclado_principal()
    )

# ======================
# MAIN
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="stats"))
    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()

