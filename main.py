import os
import requests
import math
import csv
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
# ELO BASE
# ======================================================

ELO_BASE = 1500
K = 20
HOME_ADV = 80

ratings = {}

def get_elo(team):
    return ratings.get(team, ELO_BASE)


def update_elo(home, away, result):
    ra = get_elo(home)
    rb = get_elo(away)

    ea = 1 / (1 + 10 ** ((rb - ra) / 400))

    if result == "H":
        sa = 1
    elif result == "D":
        sa = 0.5
    else:
        sa = 0

    ra_new = ra + K * (sa - ea)
    rb_new = rb + K * ((1 - sa) - (1 - ea))

    ratings[home] = ra_new
    ratings[away] = rb_new


# ======================================================
# CSV + ROI
# ======================================================

CSV_FILE = "historial_apuestas.csv"

def guardar_csv(row):
    existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        if not existe:
            w.writerow(["fecha","partido","mercado","prob"])

        w.writerow(row)


# ======================================================
# POISSON
# ======================================================

def poisson(l, k):
    return (math.exp(-l) * (l**k)) / math.factorial(k)


def over_prob(xg, line):
    p = 0
    for i in range(int(line)+1):
        p += poisson(xg, i)
    return 1 - p


def btts_prob(xg_h, xg_a):
    return 1 - (poisson(xg_h,0) + poisson(xg_a,0) - poisson(xg_h,0)*poisson(xg_a,0))


# ======================================================
# API
# ======================================================

def partidos_de_hoy():

    fecha = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")

    r = requests.get(
        URL_MATCHES,
        headers=HEADERS,
        params={"dateFrom": fecha, "dateTo": fecha},
        timeout=20
    )

    return r.json().get("matches", [])


# ======================================================
# MODELO PROFESIONAL
# ======================================================

def analizar_partido(m):

    home = m["homeTeam"]["name"]
    away = m["awayTeam"]["name"]
    comp = m["competition"]["name"]

    utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00"))
    local = utc.astimezone(ZONA_COLOMBIA)

    fecha = local.strftime("%d/%m/%Y")
    hora = local.strftime("%I:%M %p")

    elo_h = get_elo(home) + HOME_ADV
    elo_a = get_elo(away)

    diff = elo_h - elo_a

    xg_home = 1.4 + diff/400
    xg_away = 1.1 - diff/400

    xg_total = xg_home + xg_away

    p_home = 1/(1+10**(-diff/400))
    p_away = 1 - p_home
    p_draw = 0.25

    over15 = over_prob(xg_total,1)
    over25 = over_prob(xg_total,2)
    over35 = over_prob(xg_total,3)
    btts = btts_prob(xg_home,xg_away)

    mercados = {
        "Local gana": p_home,
        "Visitante gana": p_away,
        "Empate": p_draw,
        "Over 1.5": over15,
        "Over 2.5": over25,
        "Over 3.5": over35,
        "Ambos marcan": btts
    }

    mejor = max(mercados, key=mercados.get)
    prob = round(mercados[mejor]*100)

    guardar_csv([fecha, f"{home} vs {away}", mejor, prob])

    texto = f"""
🔥 <b>ANÁLISIS CUANTITATIVO – FÚTBOL</b>

🏆 {comp}
⚽ {home} vs {away}
📅 {fecha}
🕒 {hora} (COL)

📊 <b>Probabilidades reales:</b>
• Local: {round(p_home*100)}%
• Empate: {round(p_draw*100)}%
• Visitante: {round(p_away*100)}%
• Over2.5: {round(over25*100)}%
• BTTS: {round(btts*100)}%

🎯 <b>Mejor mercado:</b>
👉 {mejor} ({prob}%)

🧠 Modelo: Poisson + Elo
"""

    return texto


# ======================================================
# BOT
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]])

    await update.message.reply_text("🤖 Bot activo", reply_markup=kb)


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    partidos = partidos_de_hoy()

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]])

    if not partidos:
        await q.message.reply_text("⚠️ No hay partidos hoy", reply_markup=kb)
        return

    for m in partidos[:3]:
        texto = analizar_partido(m)
        await q.message.reply_text(texto, parse_mode="HTML", reply_markup=kb)


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
