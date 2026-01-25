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
URL_PREDICCIONES = "https://v3.football.api-sports.io/predictions"

# ======================================================
# LOGS
# ======================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ======================================================
# CACHE + ANTI SPAM
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300  # 5 minutos

ULTIMO_USO = {}
COOLDOWN = 10  # segundos

# ======================================================
# LIGAS
# ======================================================

LIGAS = [239, 39, 140, 135, 78, 61, 2, 3, 13, 71, 128, 253, 262, 1]

# ======================================================
# UTILIDADES IMAGEN
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
        f_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        f_liga = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        f_texto = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        f_prob = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
    except:
        f_titulo = f_liga = f_texto = f_prob = ImageFont.load_default()

    draw.text((40, 20), "TOP 5 APUESTAS DEL DÍA (PRUEBA)", font=f_titulo, fill="white")
    draw.text((40, 90), f"Hora Colombia: {hora}", font=f_liga, fill="white")

    colores = [(70,120,200), (40,90,160), (20,130,80), (150,80,20), (120,40,90)]

    y = 150

    for i, r in enumerate(top):

        card = Image.new("RGB", (ancho - 60, 110), colores[i % len(colores)])
        img.paste(card, (30, y))

        liga_logo = descargar_logo(r["liga_logo"], (70, 70))
        home_logo = descargar_logo(r["home_logo"], (55, 55))
        away_logo = descargar_logo(r["away_logo"], (55, 55))

        img.paste(liga_logo, (45, y + 20))
        img.paste(home_logo, (140, y + 40))
        img.paste(away_logo, (210, y + 40))

        draw.text((45, y - 2), f"{r['liga']} • {r['pais']}", font=f_liga, fill="yellow")
        draw.text((280, y + 35), f"{r['partido']} | {r['mercado']}", font=f_texto, fill="white")
        draw.text((850, y + 30), f"{r['prob']}%", font=f_prob, fill="gold")

        y += 130

    path = "top5.png"
    img.save(path)
    return path

# ======================================================
# API
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


def prediccion(fid):
    try:
        r = requests.get(
            URL_PREDICCIONES,
            headers=HEADERS,
            params={"fixture": fid},
            timeout=15
        )
        return r.json()["response"][0]
    except:
        return None

# ======================================================
# LÓGICA PRINCIPAL
# ======================================================

def generar_analisis():

    ahora = time.time()

    if CACHE_ANALISIS["texto"] and ahora - CACHE_ANALISIS["timestamp"] < CACHE_TIEMPO:
        return CACHE_ANALISIS["texto"], CACHE_ANALISIS["imagen"]

    hora = datetime.now(ZONA_COLOMBIA).strftime("%d/%m/%Y %I:%M %p")

    resultados = []

    for p in partidos_de_hoy():

        pred = prediccion(p["fixture"]["id"])
        if not pred:
            continue

        porcentajes = pred["predictions"]["percent"]
        mejor = max(porcentajes, key=lambda k: int(porcentajes[k].replace("%", "")))
        prob = int(porcentajes[mejor].replace("%", ""))

        # 🔥 UMBRAL BAJO SOLO PARA PRUEBA
        if prob >= 30:
            resultados.append({
                "liga": p["league"]["name"],
                "pais": p["league"]["country"],
                "liga_logo": p["league"]["logo"],
                "home_logo": p["teams"]["home"]["logo"],
                "away_logo": p["teams"]["away"]["logo"],
                "partido": f'{p["teams"]["home"]["name"]} vs {p["teams"]["away"]["name"]}',
                "mercado": mejor,
                "prob": prob
            })

    if not resultados:
        return "⚠️ No hay datos hoy.", None

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    texto = "🔥 <b>TOP 5 APUESTAS DEL DÍA (MODO PRUEBA)</b>\n\n"
    for r in top:
        texto += f"{r['partido']} → {r['prob']}%\n"

    imagen = crear_imagen_top5(top, hora)

    CACHE_ANALISIS.update({
        "texto": texto,
        "imagen": imagen,
        "timestamp": ahora
    })

    return texto, imagen

# ======================================================
# HANDLERS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])

    await update.message.reply_text(
        "🤖 Bot activo\nGenerando estadísticas...",
        reply_markup=teclado
    )

    texto, imagen = generar_analisis()

    if imagen:
        await update.message.reply_photo(
            photo=open(imagen, "rb"),
            caption=texto,
            parse_mode="HTML",
            reply_markup=teclado
        )
    else:
        await update.message.reply_text(texto, reply_markup=teclado)


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user.id
    ahora = time.time()

    if user in ULTIMO_USO and ahora - ULTIMO_USO[user] < COOLDOWN:
        return

    ULTIMO_USO[user] = ahora

    texto, imagen = generar_analisis()

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]
    ])

    if imagen:
        await q.message.reply_photo(
            photo=open(imagen, "rb"),
            caption=texto,
            parse_mode="HTML",
            reply_markup=teclado
        )
    else:
        await q.message.reply_text(texto, reply_markup=teclado)

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
