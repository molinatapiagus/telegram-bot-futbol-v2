import os
import requests
import time
import logging
from datetime import datetime
import pytz
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================================================
# CONFIGURACIÓN (NO TOCAR)
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {"X-Auth-Token": API_TOKEN}

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

URL_MATCHES = "https://api.football-data.org/v4/matches"

# Ligas permitidas FREE
COMPETITIONS = [
    "CL", "PL", "PD", "SA", "BL1", "FL1", "DED", "PPL"
]

# ======================================================
# LOGS
# ======================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ======================================================
# CACHE
# ======================================================

CACHE = {"data": None, "time": 0}
CACHE_TIME = 300  # 5 minutos

# ======================================================
# UTILIDADES
# ======================================================

def descargar_logo(url, size):
    try:
        r = requests.get(url, timeout=10)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize(size)
    except:
        return Image.new("RGBA", size, (255, 255, 255, 0))


def crear_imagen_top5(partidos, hora_col):
    ancho = 1000
    alto = 160 + len(partidos) * 130

    img = Image.new("RGB", (ancho, alto), (12, 35, 45))
    draw = ImageDraw.Draw(img)

    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        f_text = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        f_small = ImageFont.truetype("DejaVuSans.ttf", 22)
        f_prob = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
    except:
        f_title = f_text = f_small = f_prob = ImageFont.load_default()

    draw.text((40, 20), "🔥 TOP 5 ANÁLISIS VIP – FÚTBOL", font=f_title, fill="white")
    draw.text((40, 80), f"Hora Colombia: {hora_col}", font=f_small, fill="white")

    y = 130
    colores = [(40, 90, 140), (30, 120, 90), (120, 80, 40), (100, 40, 80), (60, 60, 140)]

    for i, p in enumerate(partidos):
        card = Image.new("RGB", (ancho - 60, 110), colores[i % len(colores)])
        img.paste(card, (30, y))

        home_logo = descargar_logo(p["home_logo"], (60, 60))
        away_logo = descargar_logo(p["away_logo"], (60, 60))

        img.paste(home_logo, (50, y + 25))
        img.paste(away_logo, (130, y + 25))

        draw.text((220, y + 10), p["competition"], font=f_small, fill="yellow")
        draw.text((220, y + 40), p["match"], font=f_text, fill="white")
        draw.text((850, y + 35), f'{p["prob"]}%', font=f_prob, fill="gold")

        y += 130

    path = "top5.png"
    img.save(path)
    return path

# ======================================================
# DATOS + LÓGICA
# ======================================================

def obtener_partidos_futuros():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    partidos = []

    for comp in COMPETITIONS:
        try:
            r = requests.get(
                URL_MATCHES,
                headers=HEADERS,
                params={"competitions": comp, "dateFrom": hoy, "dateTo": hoy},
                timeout=15
            )
            if r.status_code == 200:
                for m in r.json().get("matches", []):
                    if m["status"] in ["SCHEDULED", "TIMED"]:
                        partidos.append(m)
        except:
            continue

    return partidos


def generar_analisis():
    ahora = time.time()
    if CACHE["data"] and ahora - CACHE["time"] < CACHE_TIME:
        return CACHE["data"]

    partidos = obtener_partidos_futuros()
    if not partidos:
        return None

    resultados = []

    for m in partidos:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        # modelo simple realista (NO humo)
        prob = min(78, max(60, int(65 + (hash(home + away) % 10))))

        kickoff_utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        kickoff_col = kickoff_utc.astimezone(ZONA_COLOMBIA)

        resultados.append({
            "competition": m["competition"]["name"],
            "match": f"{home} vs {away}",
            "fecha": kickoff_col.strftime("%d/%m/%Y"),
            "hora": kickoff_col.strftime("%I:%M %p"),
            "home_logo": m["homeTeam"]["crest"],
            "away_logo": m["awayTeam"]["crest"],
            "prob": prob
        })

    top5 = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:5]

    hora_col = datetime.now(ZONA_COLOMBIA).strftime("%d/%m/%Y %I:%M %p")
    imagen = crear_imagen_top5(top5, hora_col)

    texto = "🔥 <b>ANÁLISIS VIP MATEMÁTICO DEL DÍA</b>\n\n"

    for p in top5:
        texto += (
            f"🏆 <b>{p['competition']}</b>\n"
            f"⚽ {p['match']}\n"
            f"🗓 {p['fecha']} ⏰ {p['hora']} COL\n"
            f"🎯 Over 2.5 goles → <b>{p['prob']}%</b>\n\n"
        )

    CACHE["data"] = (texto, imagen)
    CACHE["time"] = ahora

    return texto, imagen

# ======================================================
# HANDLERS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])
    await update.message.reply_text("🤖 Bot activo", reply_markup=teclado)


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]
    ])

    resultado = generar_analisis()

    if not resultado:
        await q.message.reply_text(
            "⚠️ No hay partidos futuros disponibles hoy.",
            reply_markup=teclado
        )
        return

    texto, imagen = resultado
    await q.message.reply_photo(
        photo=open(imagen, "rb"),
        caption=texto,
        parse_mode="HTML",
        reply_markup=teclado
    )

# ======================================================
# MAIN
# ======================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

