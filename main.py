import os
import requests
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


# ======================================================
# CONFIG
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
TOKEN_FOOTBALL = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": TOKEN_FOOTBALL
}


# ======================================================
# CACHE
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300


# ======================================================
# TECLADO
# ======================================================

def teclado():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])


# ======================================================
# IMAGEN
# ======================================================

def crear_imagen_top5(top):

    img = Image.new("RGB", (900, 500), (12, 40, 30))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except:
        font = ImageFont.load_default()

    y = 40
    for r in top:
        texto = f"{r['partido']} | {r['mercado']} | {r['prob']}%"
        draw.text((40, y), texto, font=font, fill="white")
        y += 60

    path = "top5.png"
    img.save(path)
    return path


# ======================================================
# PARTIDOS REALES (UTC ±1 día)
# ======================================================

def partidos_de_hoy():

    fechas = [
        datetime.utcnow().date() - timedelta(days=1),
        datetime.utcnow().date(),
        datetime.utcnow().date() + timedelta(days=1)
    ]

    partidos = []

    for f in fechas:
        url = f"{BASE_URL}/matches?dateFrom={f}&dateTo={f}"

        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            partidos.extend(r.json().get("matches", []))

    return partidos


# ======================================================
# HISTÓRICO REAL DEL EQUIPO
# ======================================================

def promedio_goles(team_id):

    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit=10"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return 1.2, 1.2

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

    if not matches:
        return 1.2, 1.2

    return gf / len(matches), gc / len(matches)


# ======================================================
# 🔥 POISSON REAL
# ======================================================

def poisson(lmbda, k):
    return (lmbda ** k * math.exp(-lmbda)) / math.factorial(k)


def prob_over25(goles):
    prob = sum(poisson(goles, i) for i in range(3))
    return int((1 - prob) * 100)


def prob_over15(goles):
    prob = sum(poisson(goles, i) for i in range(2))
    return int((1 - prob) * 100)


def prob_ambos(l1, l2):
    p1 = 1 - poisson(l1, 0)
    p2 = 1 - poisson(l2, 0)
    return int(p1 * p2 * 100)


# ======================================================
# LÓGICA PRINCIPAL
# ======================================================

def generar_analisis():

    ahora = time.time()

    if CACHE_ANALISIS["texto"] and ahora - CACHE_ANALISIS["timestamp"] < CACHE_TIEMPO:
        return CACHE_ANALISIS["texto"], CACHE_ANALISIS["imagen"]

    resultados = []

    for m in partidos_de_hoy():

        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        home_id = m["homeTeam"]["id"]
        away_id = m["awayTeam"]["id"]

        gf_h, gc_h = promedio_goles(home_id)
        gf_a, gc_a = promedio_goles(away_id)

        goles_local = (gf_h + gc_a) / 2
        goles_visit = (gf_a + gc_h) / 2
        total = goles_local + goles_visit

        mercados = {
            "Over 1.5": prob_over15(total),
            "Over 2.5": prob_over25(total),
            "Ambos marcan": prob_ambos(goles_local, goles_visit)
        }

        mejor = max(mercados, key=mercados.get)

        resultados.append({
            "partido": f"{home} vs {away}",
            "mercado": mejor,
            "prob": mercados[mejor]
        })

    if not resultados:
        return "⚠️ No hay partidos hoy.", None

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    texto = "🔥 <b>TOP 5 PROBABILIDADES REALES</b>\n\n"

    for r in top:
        texto += f"{r['partido']} → {r['mercado']} {r['prob']}%\n"

    imagen = crear_imagen_top5(top)

    CACHE_ANALISIS.update({
        "texto": texto,
        "imagen": imagen,
        "timestamp": ahora
    })

    return texto, imagen


# ======================================================
# TELEGRAM
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo", reply_markup=teclado())


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    texto, imagen = generar_analisis()

    if imagen:
        await q.message.reply_photo(photo=open(imagen, "rb"), caption=texto, parse_mode="HTML", reply_markup=teclado())
    else:
        await q.message.reply_text(texto, reply_markup=teclado())


# ======================================================
# MAIN
# ======================================================

def main():

    app = Application.builder().token(TOKEN_BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    app.run_polling()


if __name__ == "__main__":
    main()
