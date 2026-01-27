import os
import requests
import time
import logging
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


# ======================================================
# CONFIGURACIÓN
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
TOKEN_FOOTBALL = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": TOKEN_FOOTBALL
}


# ======================================================
# LOGS
# ======================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ======================================================
# CACHE + COOLDOWN
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300

ULTIMO_USO = {}
COOLDOWN = 10


# ======================================================
# IMAGEN SIMPLE
# ======================================================

def crear_imagen_top5(top):

    img = Image.new("RGB", (900, 500), (12, 40, 30))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
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
# 🔥 FOOTBALL-DATA (ARREGLADO UTC ±1 DÍA)
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

        try:
            r = requests.get(url, headers=HEADERS, timeout=20)

            if r.status_code == 200:
                partidos.extend(r.json().get("matches", []))

        except:
            pass

    return partidos


# ======================================================
# 🔥 MOTOR PREDICCIÓN LOCAL (SIN API PAGA)
# ======================================================

import random

def calcular_probabilidades():

    mercados = {
        "Over 1.5": random.randint(60, 90),
        "Over 2.5": random.randint(45, 80),
        "Gol local": random.randint(55, 90),
        "Ambos marcan": random.randint(50, 85)
    }

    mejor = max(mercados, key=mercados.get)
    return mejor, mercados[mejor]


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

        mercado, prob = calcular_probabilidades()

        resultados.append({
            "partido": f"{home} vs {away}",
            "mercado": mercado,
            "prob": prob
        })

    if not resultados:
        return "⚠️ No hay partidos disponibles en este momento.", None

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    texto = "🔥 <b>TOP 5 APUESTAS DEL DÍA (FREE)</b>\n\n"
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
# TECLADO (SIEMPRE REAPARECE)
# ======================================================

def teclado():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])


# ======================================================
# HANDLERS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo", reply_markup=teclado())


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user.id
    ahora = time.time()

    if user in ULTIMO_USO and ahora - ULTIMO_USO[user] < COOLDOWN:
        return

    ULTIMO_USO[user] = ahora

    texto, imagen = generar_analisis()

    if imagen:
        await q.message.reply_photo(
            photo=open(imagen, "rb"),
            caption=texto,
            parse_mode="HTML",
            reply_markup=teclado()
        )
    else:
        await q.message.reply_text(texto, reply_markup=teclado())


# ======================================================
# MAIN
# ======================================================

def main():

    if not TOKEN_BOT or not TOKEN_FOOTBALL:
        raise ValueError("Faltan variables de entorno")

    app = Application.builder().token(TOKEN_BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()

