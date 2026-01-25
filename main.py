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
# CONFIGURACIÓN GENERAL (NO TOCAR)
# ======================================================

TOKEN_BOT = os.getenv("BOT_TOKEN")
CLAVE_API = os.getenv("API_FOOTBALL_KEY")

ZONA_COLOMBIA = pytz.timezone("America/Bogota")

HEADERS = {
    "x-apisports-key": CLAVE_API
}

URL_PARTIDOS = "https://v3.football.api-sports.io/fixtures"
URL_PREDICCIONES = "https://v3.football.api-sports.io/predictions"
URL_CUOTAS = "https://v3.football.api-sports.io/odds"


# ======================================================
# LIGAS DISPONIBLES (puedes activar/desactivar)
# ======================================================

LIGAS = {
    "colombia": [239],
    "europa": [39, 140, 135, 78, 61, 2, 3],
    "america": [13, 71, 128, 253, 262],
    "mundial": [1, 11, 32]
}

# 👉 CAMBIA SOLO AQUÍ si quieres filtrar
FILTRO_LIGAS_ACTIVAS = ["colombia", "europa", "mundial"]


# ======================================================
# FUNCIONES API (SOLO LÓGICA)
# ======================================================

def obtener_ids_ligas():
    ids = []
    for nombre in FILTRO_LIGAS_ACTIVAS:
        ids.extend(LIGAS[nombre])
    return ids


def obtener_partidos_de_hoy():
    fecha_hoy = datetime.now(ZONA_COLOMBIA).strftime("%Y-%m-%d")
    ids_ligas = obtener_ids_ligas()

    partidos = []

    for liga in ids_ligas:
        try:
            params = {"league": liga, "date": fecha_hoy}
            r = requests.get(URL_PARTIDOS, headers=HEADERS, params=params, timeout=15)
            datos = r.json().get("response", [])
            partidos.extend(datos)
        except:
            pass

    return partidos


def obtener_prediccion(id_partido):
    try:
        r = requests.get(
            URL_PREDICCIONES,
            headers=HEADERS,
            params={"fixture": id_partido},
            timeout=15
        )
        return r.json().get("response", [])[0]
    except:
        return None


def obtener_cuotas(id_partido):
    try:
        r = requests.get(
            URL_CUOTAS,
            headers=HEADERS,
            params={"fixture": id_partido},
            timeout=15
        )
        datos = r.json().get("response", [])
        if datos:
            return datos[0]["bookmakers"][0]["bets"][0]["values"]
        return []
    except:
        return []


# ======================================================
# 🔥 FUNCIÓN PRINCIPAL (ÚNICA QUE MODIFICAMOS)
# ======================================================

def generar_analisis():

    hora_actual = datetime.now(ZONA_COLOMBIA).strftime("%d/%m/%Y %I:%M %p")

    partidos = obtener_partidos_de_hoy()

    resultados = []

    for p in partidos:

        pred = obtener_prediccion(p["fixture"]["id"])
        if not pred:
            continue

        try:
            porcentajes = {
                "Local": int(pred["predictions"]["percent"]["home"].replace("%","")),
                "Empate": int(pred["predictions"]["percent"]["draw"].replace("%","")),
                "Visitante": int(pred["predictions"]["percent"]["away"].replace("%","")),
                "Más de 2.5 goles": int(pred["predictions"]["percent"]["over_2.5"].replace("%","")),
                "Ambos marcan": int(pred["predictions"]["percent"]["btts"].replace("%",""))
            }

            mercado_mejor = max(porcentajes, key=porcentajes.get)
            probabilidad = porcentajes[mercado_mejor]

            # 🔒 SOLO apuestas seguras >= 70%
            if probabilidad < 70:
                continue

            cuotas = obtener_cuotas(p["fixture"]["id"])
            mejor_cuota = cuotas[0]["odd"] if cuotas else "N/A"

            resultados.append({
                "liga": p["league"]["name"],
                "hora": p["fixture"]["date"][11:16],
                "partido": f'{p["teams"]["home"]["name"]} vs {p["teams"]["away"]["name"]}',
                "mercado": mercado_mejor,
                "prob": probabilidad,
                "cuota": mejor_cuota
            })

        except:
            continue

    if not resultados:
        return "⚠️ No hay apuestas seguras hoy."

    # TOP 3
    top = sorted(resultados, key=lambda x: x["prob"], reverse=True)[:3]

    texto = f"🔥 <b>TOP 3 APUESTAS SEGURAS DEL DÍA</b>\n"
    texto += f"🕒 Hora Colombia: {hora_actual}\n\n"

    for i, r in enumerate(top, 1):
        texto += f"""
{i}️⃣ <b>{r['liga']}</b>
⚽ {r['partido']}
⏰ {r['hora']}
📊 {r['mercado']} → <b>{r['prob']}%</b>
💰 Cuota: {r['cuota']}
"""

    return texto


# ======================================================
# HANDLERS (NO TOCAR)
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [[InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]]
    await update.message.reply_text(
        "🤖 Bot activo y estable\nPulsa el botón:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    texto = generar_analisis()

    teclado = [[InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]]
    await query.message.reply_text(
        texto,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


# ======================================================
# ARQUITECTURA ESTABLE (NO TOCAR)
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot estable en polling puro")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
