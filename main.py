import os
import requests
import math
import time
import pytz
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================================================
# CONFIG
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {"X-Auth-Token": API_TOKEN}

BASE = "https://api.football-data.org/v4"

ZONA = pytz.timezone("America/Bogota")

CACHE = {"data": None, "ts": 0}
CACHE_TIME = 300

COOLDOWN = {}

# ======================================================
# LIGAS GRATIS DISPONIBLES (football-data free)
# ======================================================

COMPETITIONS = [
    "PL",    # Premier
    "CL",    # Champions
    "PD",    # La Liga
    "BL1",   # Bundesliga
    "SA",    # Serie A
    "FL1"    # Ligue 1
]

# ======================================================
# UTILIDADES MATEMÁTICAS
# ======================================================

def poisson(lmbda, k):
    return (lmbda**k * math.exp(-lmbda)) / math.factorial(k)


def prob_over25(lmbda):
    total = 0
    for i in range(3):
        total += poisson(lmbda, i)
    return 1 - total


def prob_btts(l1, l2):
    p_no_home = poisson(l1, 0)
    p_no_away = poisson(l2, 0)
    return 1 - (p_no_home + p_no_away - (p_no_home * p_no_away))


# ======================================================
# API
# ======================================================

def partidos_hoy():
    hoy = datetime.now(ZONA).strftime("%Y-%m-%d")
    partidos = []

    for c in COMPETITIONS:
        try:
            r = requests.get(
                f"{BASE}/competitions/{c}/matches",
                headers=HEADERS,
                params={"dateFrom": hoy, "dateTo": hoy}
            )
            partidos += r.json().get("matches", [])
        except:
            pass

    return partidos


def historial(team_id):

    try:
        r = requests.get(
            f"{BASE}/teams/{team_id}/matches",
            headers=HEADERS,
            params={"limit": 10, "status": "FINISHED"}
        )

        matches = r.json().get("matches", [])

        gf = 0
        gc = 0

        for m in matches:
            if m["homeTeam"]["id"] == team_id:
                gf += m["score"]["fullTime"]["home"]
                gc += m["score"]["fullTime"]["away"]
            else:
                gf += m["score"]["fullTime"]["away"]
                gc += m["score"]["fullTime"]["home"]

        if len(matches) == 0:
            return 1.2, 1.2

        return gf/len(matches), gc/len(matches)

    except:
        return 1.2, 1.2


# ======================================================
# ELO SIMPLE
# ======================================================

ELO = {}

def elo(team):
    return ELO.get(team, 1500)


def elo_prob(e1, e2):
    return 1/(1+10**((e2-e1)/400))


# ======================================================
# MOTOR DE PREDICCIÓN
# ======================================================

def generar():

    now = time.time()

    if CACHE["data"] and now - CACHE["ts"] < CACHE_TIME:
        return CACHE["data"]

    texto = "🔥 <b>ANÁLISIS MATEMÁTICO DEL DÍA</b>\n\n"

    partidos = partidos_hoy()

    if not partidos:
        return "⚠️ No hay partidos hoy.", None

    for p in partidos[:5]:

        home_id = p["homeTeam"]["id"]
        away_id = p["awayTeam"]["id"]

        gf_h, gc_h = historial(home_id)
        gf_a, gc_a = historial(away_id)

        lambda_home = (gf_h + gc_a)/2
        lambda_away = (gf_a + gc_h)/2

        total_lambda = lambda_home + lambda_away

        over25 = prob_over25(total_lambda)
        btts = prob_btts(lambda_home, lambda_away)

        e1 = elo(home_id)
        e2 = elo(away_id)
        win_home = elo_prob(e1, e2)

        mejor = max([
            ("Over 2.5 goles", over25),
            ("Ambos marcan", btts),
            ("Gana local", win_home)
        ], key=lambda x: x[1])

        if mejor[1] < 0.60:
            continue

        hora = datetime.fromisoformat(p["utcDate"].replace("Z","+00:00")).astimezone(ZONA)

        texto += (
            f"🏆 {p['competition']['name']}\n"
            f"⚽ {p['homeTeam']['name']} vs {p['awayTeam']['name']}\n"
            f"🕒 {hora.strftime('%d/%m %H:%M')} COL\n"
            f"🎯 {mejor[0]} → {int(mejor[1]*100)}%\n\n"
        )

    CACHE["data"] = (texto, None)
    CACHE["ts"] = now

    return texto, None


# ======================================================
# TELEGRAM
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]])

    await update.message.reply_text("Bot activo", reply_markup=kb)


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if uid in COOLDOWN and time.time()-COOLDOWN[uid] < 5:
        return

    COOLDOWN[uid] = time.time()

    texto, _ = generar()

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]])

    await q.message.reply_text(texto, parse_mode="HTML", reply_markup=kb)


# ======================================================
# MAIN
# ======================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling()


if __name__ == "__main__":
    main()

