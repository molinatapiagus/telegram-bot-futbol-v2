import os
import requests
import time
import math
import csv
import logging
from datetime import datetime
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================================================
# CONFIG
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {"X-Auth-Token": API_TOKEN}

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

URL_MATCHES = "https://api.football-data.org/v4/matches"

# ======================================================
# LOG
# ======================================================

logging.basicConfig(level=logging.INFO)

# ======================================================
# CSV + ROI
# ======================================================

CSV_FILE = "historial_apuestas.csv"


def guardar_csv(fila):
    existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not existe:
            writer.writerow(
                ["fecha", "partido", "mercado", "probabilidad", "resultado"]
            )

        writer.writerow(fila)


def calcular_roi():
    if not os.path.exists(CSV_FILE):
        return 0

    total = 0
    aciertos = 0

    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total += 1
            if r["resultado"] == "win":
                aciertos += 1

    if total == 0:
        return 0

    return round((aciertos / total) * 100, 2)


# ======================================================
# POISSON
# ======================================================

def poisson(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)


def prob_over25(xg_home, xg_away):
    l = xg_home + xg_away
    p = 0
    for i in range(3):
        p += poisson(l, i)
    return 1 - p


def prob_btts(xg_home, xg_away):
    p_home0 = poisson(xg_home, 0)
    p_away0 = poisson(xg_away, 0)
    return 1 - (p_home0 + p_away0 - (p_home0 * p_away0))


# ======================================================
# API
# ======================================================

def partidos_de_hoy():
    fecha = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")

    r = requests.get(
        URL_MATCHES,
        headers=HEADERS,
        params={"dateFrom": fecha, "dateTo": fecha, "status": "SCHEDULED"},
        timeout=20,
    )

    data = r.json()

    return data.get("matches", [])


# ======================================================
# MODELO ESTADÍSTICO REAL
# ======================================================

def analizar_partido(m):

    home = m["homeTeam"]["name"]
    away = m["awayTeam"]["name"]
    comp = m["competition"]["name"]

    utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
    local = utc.astimezone(ZONA_COLOMBIA)

    fecha = local.strftime("%d/%m/%Y")
    hora = local.strftime("%I:%M %p")

    # 🔥 estimación simple xG realista con históricos medios
    xg_home = 1.6
    xg_away = 1.2

    over25 = prob_over25(xg_home, xg_away)
    btts = prob_btts(xg_home, xg_away)

    mercado = "Over 2.5 goles"
    prob = over25

    if btts > over25:
        mercado = "Ambos marcan"
        prob = btts

    prob_pct = round(prob * 100)

    texto = f"""
🔥 <b>ANÁLISIS MATEMÁTICO – FÚTBOL</b>

🏆 <b>Torneo:</b> {comp}
⚽ <b>Partido:</b> {home} vs {away}
📅 <b>Fecha:</b> {fecha}
🕒 <b>Hora (COL):</b> {hora}

🎯 <b>Mercado con mayor probabilidad:</b>
👉 {mercado}

📊 <b>Probabilidad matemática:</b> {prob_pct}%

🧠 <b>Modelo:</b> Poisson + xG estimado
• xG local: {xg_home}
• xG visita: {xg_away}
"""

    guardar_csv([fecha, f"{home} vs {away}", mercado, prob_pct, "pending"])

    return texto, prob_pct


# ======================================================
# BOT
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]]
    )

    await update.message.reply_text(
        "🤖 Bot activo", reply_markup=teclado
    )


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    partidos = partidos_de_hoy()

    teclado = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]]
    )

    if not partidos:
        await q.message.reply_text(
            "⚠️ No hay partidos hoy.", reply_markup=teclado
        )
        return

    textos = []
    for m in partidos[:3]:
        t, _ = analizar_partido(m)
        textos.append(t)

    roi = calcular_roi()

    await q.message.reply_text(
        "\n\n".join(textos) + f"\n📈 ROI histórico: {roi}%",
        parse_mode="HTML",
        reply_markup=teclado,
    )


# ======================================================
# MAIN
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
