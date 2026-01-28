import os
import requests
import time
import logging
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


# ======================================================
# CONFIGURACIÓN (NO TOCAR)
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


# ======================================================
# CACHE + ANTI SPAM (igual que tu estructura original)
# ======================================================

CACHE_ANALISIS = {"texto": None, "imagen": None, "timestamp": 0}
CACHE_TIEMPO = 300

ULTIMO_USO = {}
COOLDOWN = 10


# ======================================================
# TECLADO (SIEMPRE REAPARECE)
# ======================================================

def teclado():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])


# ======================================================
# IMAGEN SIMPLE (misma idea que tu bot)
# ======================================================

def crear_imagen_top5(top):

    ancho = 900
    alto = 120 + len(top) * 80

    img = Image.new("RGB", (ancho, alto), (12, 40, 30))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
    except:
        font = ImageFont.load_default()

    y = 40

    for r in top:
        texto = f"{r}"
        draw.text((40, y), texto, font=font, fill="white")
        y += 70

    path = "top5.png"
    img.save(path)
    return path


# ======================================================
# PARTIDOS REALES DESDE FOOTBALL-DATA
# ======================================================

def partidos_reales():

    # MUCHÍSIMO MÁS CONFIABLE QUE FILTRAR POR FECHA
    url = f"{BASE_URL}/matches?status=SCHEDULED"

    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        return []

    matches = r.json().get("matches", [])

    hoy = datetime.utcnow().date()

    partidos = []

    for m in matches:
        fecha = datetime.fromisoformat(
            m["utcDate"].replace("Z", "")
        ).date()

        # hoy + próximos 2 días
        if abs((fecha - hoy).days) <= 2:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            partidos.append(f"{home} vs {away}")

    return partidos


# ======================================================
# LÓGICA PRINCIPAL
# ======================================================

def generar_analisis():

    ahora = time.time()

    if CACHE_ANALISIS["texto"] and ahora - CACHE_ANALISIS["timestamp"] < CACHE_TIEMPO:
        return CACHE_ANALISIS["texto"], CACHE_ANALISIS["imagen"]

    partidos = partidos_reales()

    if not partidos:
        return "⚠️ No hay partidos próximos.", None

    top = partidos[:5]

    texto = "🔥 <b>PARTIDOS PROGRAMADOS (DATOS REALES)</b>\n\n"

    for p in top:
        texto += f"• {p}\n"

    imagen = crear_imagen_top5(top)

    CACHE_ANALISIS.update({
        "texto": texto,
        "imagen": imagen,
        "timestamp": ahora
    })

    return texto, imagen


# ======================================================
# HANDLERS TELEGRAM
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot activo",
        reply_markup=teclado()
    )


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
        raise ValueError("Faltan BOT_TOKEN o FOOTBALL_DATA_TOKEN")

    app = Application.builder().token(TOKEN_BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
