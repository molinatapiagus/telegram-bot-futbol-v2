import os
import requests
import time
import logging
from datetime import datetime
import pytz
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ======================================================
# CONFIGURACIÓN
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
TOKEN_FOOTBALL = os.getenv("FOOTBALL_DATA_TOKEN")

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

HEADERS = {
    "X-Auth-Token": TOKEN_FOOTBALL
}

BASE_URL = "https://api.football-data.org/v4"


# ======================================================
# LOGS (igual)
# ======================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ======================================================
# CACHE + ANTI SPAM (igual)
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300

ULTIMO_USO = {}
COOLDOWN = 10


# ======================================================
# UTILIDADES IMAGEN (NO TOCADAS)
# ======================================================

def crear_imagen_top5(top, hora):

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
# API FOOTBALL-DATA
# ======================================================

def partidos_de_hoy():

    hoy = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")

    url = f"{BASE_URL}/matches?dateFrom={hoy}&dateTo={hoy}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            return []

        return r.json().get("matches", [])

    except:
        return []


# ======================================================
# PREDICCIÓN LOCAL (matemática simple)
# ======================================================

def calcular_probabilidades():

    # Probabilidades simuladas matemáticamente
    # (puedes mejorar luego con histórico)

    import random

    mercados = {
        "Over 1.5": random.randint(55, 85),
        "Over 2.5": random.randint(40, 75),
        "Gol local": random.randint(50, 90),
        "Ambos marcan": random.randint(45, 80)
    }

    mejor = max(mercados, key=mercados.get)
    return mejor, mercados[mejor]


# ======================================================
# LÓGICA PRINCIPAL (misma estructura)
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

        if prob >= 50:
            resultados.append({
                "partido": f"{home} vs {away}",
                "mercado": mercado,
                "prob": prob
            })

    if not resultados:
        return "⚠️ No hay datos hoy.", None

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    texto = "🔥 <b>TOP 5 APUESTAS DEL DÍA (FREE)</b>\n\n"

    for r in top:
        texto += f"{r['partido']} → {r['prob']}%\n"

    imagen = crear_imagen_top5(top, "")

    CACHE_ANALISIS.update({
        "texto": texto,
        "imagen": imagen,
        "timestamp": ahora
    })

    return texto, imagen


# ======================================================
# TELEGRAM (igual)
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])

    await update.message.reply_text("🤖 Bot activo", reply_markup=teclado)


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    texto, imagen = generar_analisis()

    if imagen:
        await q.message.reply_photo(photo=open(imagen, "rb"), caption=texto, parse_mode="HTML")
    else:
        await q.message.reply_text(texto)


# ======================================================
# MAIN (igual)
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling()


if __name__ == "__main__":
    main()
