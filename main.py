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

# ===============================
# CONFIGURACIÓN GENERAL
# ===============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN or not FOOTBALL_API_KEY:
    raise RuntimeError("Faltan variables de entorno (BOT_TOKEN o FOOTBALL_API_KEY)")

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": FOOTBALL_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# ===============================
# TECLADO PRINCIPAL
# ===============================

def teclado_principal():
    keyboard = [
        [InlineKeyboardButton("📊 Pedir estadísticas", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===============================
# /start
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *Bot de análisis estadístico de fútbol*\n\n"
        "Pulsa el botón para analizar los partidos del día.",
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# ===============================
# OBTENER PARTIDOS DE HOY
# ===============================

def obtener_partidos_hoy():
    url = f"{API_BASE}/fixtures"
    params = {"date": context_fecha_hoy()}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)

    if r.status_code != 200:
        return []

    data = r.json()
    return data.get("response", [])

def context_fecha_hoy():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")

# ===============================
# OBTENER ESTADÍSTICAS EQUIPO
# ===============================

def obtener_estadisticas_equipo(team_id, league_id, season):
    url = f"{API_BASE}/teams/statistics"
    params = {
        "team": team_id,
        "league": league_id,
        "season": season
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)

    if r.status_code != 200:
        return None

    return r.json().get("response")

# ===============================
# CÁLCULO DE PROBABILIDADES
# ===============================

def calcular_probabilidades(stats_home, stats_away):
    try:
        goles_home = stats_home["goals"]["for"]["average"]["total"]
        goles_away = stats_away["goals"]["for"]["average"]["total"]
        total_goles = goles_home + goles_away

        over_25 = min(95, round((total_goles / 3.0) * 100))
        under_25 = 100 - over_25

        btts = min(95, round(((goles_home + goles_away) / 2.5) * 100))

        return {
            "over_25": over_25,
            "under_25": under_25,
            "btts": btts
        }
    except Exception:
        return None

# ===============================
# CALLBACK BOTÓN
# ===============================

async def pedir_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partidos = obtener_partidos_hoy()

    if not partidos:
        await query.edit_message_text(
            "❌ *Hoy no hay partidos disponibles.*\n"
            "Inténtalo más tarde.",
            reply_markup=teclado_principal(),
            parse_mode="Markdown"
        )
        return

    mensajes = []

    for partido in partidos[:5]:  # limitamos a 5 para no saturar
        home = partido["teams"]["home"]
        away = partido["teams"]["away"]
        league = partido["league"]

        stats_home = obtener_estadisticas_equipo(
            home["id"], league["id"], league["season"]
        )
        stats_away = obtener_estadisticas_equipo(
            away["id"], league["id"], league["season"]
        )

        if not stats_home or not stats_away:
            continue

        probs = calcular_probabilidades(stats_home, stats_away)
        if not probs:
            continue

        recomendacion = "Over 2.5 goles" if probs["over_25"] >= probs["btts"] else "Ambos equipos marcan"

        mensaje = (
            f"🏟 *{home['name']} vs {away['name']}*\n"
            f"📈 Over 2.5 goles: *{probs['over_25']}%*\n"
            f"📉 Under 2.5 goles: *{probs['under_25']}%*\n"
            f"⚽ Ambos marcan: *{probs['btts']}%*\n"
            f"✅ *Apuesta más segura:* {recomendacion}\n"
        )

        mensajes.append(mensaje)

    if not mensajes:
        await query.edit_message_text(
            "❌ No se pudieron calcular estadísticas hoy.",
            reply_markup=teclado_principal()
        )
        return

    texto_final = "\n\n".join(mensajes)

    await query.edit_message_text(
        texto_final,
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# ===============================
# MAIN
# ===============================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pedir_estadisticas, pattern="^stats$"))

    print("🤖 Bot iniciado correctamente (polling)")
    app.run_polling()

if __name__ == "__main__":
    main()

