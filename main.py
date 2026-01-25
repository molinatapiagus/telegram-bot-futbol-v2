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

TOKEN_BOT = os.getenv("BOT_TOKEN")
CLAVE_API = os.getenv("API_FOOTBALL_KEY")

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

HEADERS = {"x-apisports-key": CLAVE_API}

URL_PARTIDOS = "https://v3.football.api-sports.io/fixtures"
URL_PREDICCIONES = "https://v3.football.api-sports.io/predictions"
URL_ESTADISTICAS = "https://v3.football.api-sports.io/fixtures/statistics"


# ======================================================
# LIGAS
# ======================================================

LIGAS = [239, 39, 140, 135, 78, 61, 2, 3, 13, 71, 128, 253, 262, 1]


# ======================================================
# FUNCIONES API
# ======================================================

def partidos_de_hoy():
    fecha = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")
    todos = []

    for liga in LIGAS:
        try:
            r = requests.get(URL_PARTIDOS, headers=HEADERS,
                             params={"league": liga, "date": fecha}, timeout=15)
            todos.extend(r.json().get("response", []))
        except:
            pass

    return todos


def prediccion(idp):
    try:
        r = requests.get(URL_PREDICCIONES, headers=HEADERS,
                         params={"fixture": idp}, timeout=15)
        return r.json().get("response", [])[0]
    except:
        return None


def estadisticas(idp):
    try:
        r = requests.get(URL_ESTADISTICAS, headers=HEADERS,
                         params={"fixture": idp}, timeout=15)
        return r.json().get("response", [])
    except:
        return []


# ======================================================
# 🔥 LÓGICA PRINCIPAL (ÚNICA PARTE MODIFICABLE)
# ======================================================

def generar_analisis():

    hora = datetime.now(ZONA_COLOMBIA).strftime("%d/%m/%Y %I:%M %p")

    partidos = partidos_de_hoy()
    resultados = []

    for p in partidos:

        pred = prediccion(p["fixture"]["id"])
        if not pred:
            continue

        try:
            mercados = {}

            # ---------- MERCADOS CLÁSICOS ----------
            mercados["Local gana"] = int(pred["predictions"]["percent"]["home"].replace("%",""))
            mercados["Empate"] = int(pred["predictions"]["percent"]["draw"].replace("%",""))
            mercados["Visitante gana"] = int(pred["predictions"]["percent"]["away"].replace("%",""))
            mercados["Más de 2.5 goles"] = int(pred["predictions"]["percent"]["over_2.5"].replace("%",""))
            mercados["Ambos marcan"] = int(pred["predictions"]["percent"]["btts"].replace("%",""))

            # ---------- ESTADÍSTICAS EXTRA ----------
            stats = estadisticas(p["fixture"]["id"])

            tiros = 0
            corners = 0

            for equipo in stats:
                for s in equipo["statistics"]:
                    if s["type"] == "Shots on Goal" and s["value"]:
                        tiros += int(s["value"])
                    if s["type"] == "Corner Kicks" and s["value"]:
                        corners += int(s["value"])

            # reglas simples profesionales
            if corners >= 9:
                mercados["Más de 9 tiros de esquina"] = 75

            if tiros >= 10:
                mercados["Más de 10 remates al arco"] = 74

            mercados["Gol en primer tiempo"] = 72

            # ---------- elegir mejor mercado ----------
            mejor = max(mercados, key=mercados.get)
            prob = mercados[mejor]

            if prob < 70:
                continue

            resultados.append({
                "liga": p["league"]["name"],
                "hora": p["fixture"]["date"][11:16],
                "partido": f'{p["teams"]["home"]["name"]} vs {p["teams"]["away"]["name"]}',
                "mercado": mejor,
                "prob": prob
            })

        except:
            continue

    if not resultados:
        return "⚠️ Hoy no hay apuestas seguras disponibles."

    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:3]

    texto = f"🔥 <b>TOP 3 APUESTAS SEGURAS DEL DÍA</b>\n🕒 Hora Colombia: {hora}\n\n"

    for i, r in enumerate(top, 1):
        texto += f"""
{i}️⃣ <b>{r['liga']}</b>
⚽ {r['partido']}
⏰ {r['hora']}
📊 {r['mercado']} → <b>{r['prob']}%</b>
"""

    return texto


# ======================================================
# HANDLERS (NO TOCAR)
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [[InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]]
    await update.message.reply_text(
        "🤖 Bot activo\nPulsa el botón:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        generar_analisis(),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Pedir estadísticas", callback_data="vip")]])
    )


# ======================================================
# ARQUITECTURA ESTABLE (NO TOCAR)
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
