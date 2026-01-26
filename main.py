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
# CONFIGURACIÓN (NO TOCAR)
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
CLAVE_API = os.getenv("API_FOOTBALL_KEY")

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

HEADERS = {"x-apisports-key": CLAVE_API}

URL_PARTIDOS = "https://v3.football.api-sports.io/fixtures"

# 👉 NUEVO (estadísticas gratis del equipo)
URL_STATS = "https://v3.football.api-sports.io/teams/statistics"


# ======================================================
# LOGS
# ======================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ======================================================
# CACHE + ANTI SPAM
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300

ULTIMO_USO = {}
COOLDOWN = 10


# ======================================================
# LIGAS
# ======================================================

LIGAS = [239, 39, 140, 135, 78, 61, 2, 3, 13, 71, 128, 253, 262, 1]


# ======================================================
# UTILIDADES IMAGEN (NO TOCADO)
# ======================================================

def descargar_logo(url, size):
    try:
        r = requests.get(url, timeout=10)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize(size)
    except:
        return Image.new("RGBA", size, (255, 255, 255, 0))


def crear_imagen_top5(top, hora):

    ancho = 1000
    alto = 170 + len(top) * 130

    img = Image.new("RGB", (ancho, alto), (12, 40, 30))
    draw = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except:
        f = ImageFont.load_default()

    y = 80
    for r in top:
        draw.text((40, y), f"{r['partido']} | {r['mercado']} | {r['prob']}%", font=f, fill="white")
        y += 70

    path = "top5.png"
    img.save(path)
    return path


# ======================================================
# API PARTIDOS (IGUAL)
# ======================================================

def partidos_de_hoy():
    fecha = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")
    partidos = []

    for liga in LIGAS:
        try:
            r = requests.get(
                URL_PARTIDOS,
                headers=HEADERS,
                params={"league": liga, "date": fecha},
                timeout=15
            )
            if r.status_code == 200:
                partidos.extend(r.json().get("response", []))
        except:
            pass

    return partidos


# ======================================================
# NUEVO: ESTADÍSTICAS LOCALES
# ======================================================

def estadisticas_equipo(team_id, league_id):

    try:
        r = requests.get(
            URL_STATS,
            headers=HEADERS,
            params={"team": team_id, "league": league_id, "season": 2024},
            timeout=15
        )

        data = r.json()["response"]

        gf = float(data["goals"]["for"]["average"]["total"])
        gc = float(data["goals"]["against"]["average"]["total"])

        return gf, gc

    except:
        return 1.2, 1.2


def calcular_probabilidades(gf_local, gc_local, gf_visit, gc_visit):

    ataque_local = (gf_local + gc_visit) / 2
    ataque_visit = (gf_visit + gc_local) / 2
    total = ataque_local + ataque_visit

    mercados = {
        "Over 1.5": min(int(total * 30), 95),
        "Over 2.5": min(int(total * 18), 90),
        "Gol local": min(int(ataque_local * 45), 95),
        "Ambos marcan": min(int(total * 20), 90),
    }

    mejor = max(mercados, key=mercados.get)
    return mejor, mercados[mejor]


# ======================================================
# LÓGICA PRINCIPAL (MISMA ESTRUCTURA)
# ======================================================

def generar_analisis():

    ahora = time.time()

    if CACHE_ANALISIS["texto"] and ahora - CACHE_ANALISIS["timestamp"] < CACHE_TIEMPO:
        return CACHE_ANALISIS["texto"], CACHE_ANALISIS["imagen"]

    resultados = []

    for p in partidos_de_hoy():

        liga_id = p["league"]["id"]
        home_id = p["teams"]["home"]["id"]
        away_id = p["teams"]["away"]["id"]

        gf_local, gc_local = estadisticas_equipo(home_id, liga_id)
        gf_visit, gc_visit = estadisticas_equipo(away_id, liga_id)

        mercado, prob = calcular_probabilidades(gf_local, gc_local, gf_visit, gc_visit)

        if prob >= 40:
            resultados.append({
                "partido": f'{p["teams"]["home"]["name"]} vs {p["teams"]["away"]["name"]}',
                "mercado": mercado,
                "prob": prob
            })

    if not resultados:
        return "⚠️ No hay datos hoy.", None

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    texto = "🔥 <b>TOP 5 APUESTAS DEL DÍA (LOCAL)</b>\n\n"
    for r in top:
        texto += f"{r['partido']} → {r['mercado']} {r['prob']}%\n"

    imagen = crear_imagen_top5(top, datetime.now().strftime("%H:%M"))

    CACHE_ANALISIS.update({
        "texto": texto,
        "imagen": imagen,
        "timestamp": ahora
    })

    return texto, imagen


# ======================================================
# TELEGRAM (SIN CAMBIOS)
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
# MAIN (IGUAL)
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
