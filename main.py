import os
import requests
from datetime import datetime
import pytz

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

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

ZONA_CO = pytz.timezone("America/Bogota")

HEADERS = {
    "x-apisports-key": API_KEY
}

PRED_URL = "https://v3.football.api-sports.io/predictions"
FIX_URL = "https://v3.football.api-sports.io/fixtures"


# ======================================================
# LIGAS IMPORTANTES
# ======================================================

LEAGUES = [
    39, 140, 135, 78, 61,     # Europa top
    2, 3,                     # Champions / Europa
    13,                       # Libertadores
    71, 128, 239,             # Brasil / Argentina / Colombia
    253, 262,                 # MLS / Liga MX
    1, 11, 32                 # Mundial + eliminatorias
]


# ======================================================
# OBTENER PARTIDOS SOLO HOY (HORA COLOMBIA)
# ======================================================

def obtener_partidos_hoy():

    hoy_col = datetime.now(ZONA_CO).strftime("%Y-%m-%d")

    partidos = []

    for league in LEAGUES:
        try:
            params = {
                "league": league,
                "date": hoy_col
            }

            r = requests.get(FIX_URL, headers=HEADERS, params=params, timeout=15)
            data = r.json().get("response", [])

            partidos.extend(data)

        except:
            pass

    return partidos


# ======================================================
# OBTENER PREDICCIONES DE UN PARTIDO
# ======================================================

def obtener_prediccion(fixture_id):

    try:
        r = requests.get(
            PRED_URL,
            headers=HEADERS,
            params={"fixture": fixture_id},
            timeout=15
        )

        return r.json().get("response", [])[0]

    except:
        return None


# ======================================================
# LÓGICA PRINCIPAL (SOLO ESTA PARTE SE MODIFICA)
# ======================================================

def generar_analisis():

    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    partidos = obtener_partidos_hoy()

    if not partidos:
        return f"""
⚠️ No hay partidos disponibles hoy
🕒 Hora Colombia: {ahora}

Intenta más tarde.
"""

    analisis = []

    for p in partidos:
        pred = obtener_prediccion(p["fixture"]["id"])

        if not pred:
            continue

        try:
            home = pred["predictions"]["percent"]["home"]
            draw = pred["predictions"]["percent"]["draw"]
            away = pred["predictions"]["percent"]["away"]

            over = pred["predictions"]["percent"]["over_2.5"]
            btts = pred["predictions"]["percent"]["btts"]

            valores = {
                "Local": int(home.replace("%","")),
                "Empate": int(draw.replace("%","")),
                "Visitante": int(away.replace("%","")),
                "Más de 2.5 goles": int(over.replace("%","")),
                "Ambos marcan": int(btts.replace("%",""))
            }

            mejor_mercado = max(valores, key=valores.get)
            prob = valores[mejor_mercado]

            analisis.append({
                "liga": p["league"]["name"],
                "hora": p["fixture"]["date"][11:16],
                "partido": f'{p["teams"]["home"]["name"]} vs {p["teams"]["away"]["name"]}',
                "mercado": mejor_mercado,
                "prob": prob
            })

        except:
            continue

    if not analisis:
        return "No se pudieron calcular estadísticas."

    # 🔥 TOP 3
    top3 = sorted(analisis, key=lambda x: x["prob"], reverse=True)[:3]

    texto = f"🔥 <b>TOP 3 MEJORES PRONÓSTICOS DEL DÍA</b>\n"
    texto += f"🕒 Hora Colombia: {ahora}\n\n"

    for i, a in enumerate(top3, 1):
        texto += f"""
{i}️⃣ <b>{a['liga']}</b>
⚽ {a['partido']}
⏰ {a['hora']}
📊 {a['mercado']} → <b>{a['prob']}%</b>

"""

    return texto


# ======================================================
# HANDLERS (NO TOCAR)
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 Bot activo y estable\n\nPulsa el botón para pedir análisis:",
        reply_markup=reply_markup
    )


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    texto = generar_analisis()

    keyboard = [[InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        texto,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


# ======================================================
# ARQUITECTURA ESTABLE (NO TOCAR)
# ======================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot iniciado en polling puro (estable)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
