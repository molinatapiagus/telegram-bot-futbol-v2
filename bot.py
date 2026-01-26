import os
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =====================================================
# CONFIGURACIÓN
# =====================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FOOTBALL_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": FOOTBALL_TOKEN
}


# =====================================================
# FUNCIÓN API (ÚNICA PARTE CAMBIADA)
# =====================================================

def obtener_partidos_hoy():
    """
    Consulta football-data.org
    Devuelve lista de partidos del día
    """

    hoy = datetime.utcnow().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/matches?dateFrom={hoy}&dateTo={hoy}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            print("Error API:", r.text)
            return []

        data = r.json()
        matches = data.get("matches", [])

        partidos = []

        for m in matches:
            partidos.append({
                "hora": m["utcDate"][11:16],
                "local": m["homeTeam"]["name"],
                "visitante": m["awayTeam"]["name"],
                "estado": m["status"]
            })

        return partidos

    except Exception as e:
        print("Error consultando API:", e)
        return []


# =====================================================
# GENERADOR DE MENSAJE (MISMA LÓGICA)
# =====================================================

def generar_estadisticas():

    partidos = obtener_partidos_hoy()

    if not partidos:
        return "⚠️ No hay datos hoy."

    mensaje = "📊 Partidos de hoy:\n\n"

    for p in partidos:
        mensaje += (
            f"{p['hora']}  |  "
            f"{p['local']} vs {p['visitante']}  "
            f"({p['estado']})\n"
        )

    return mensaje


# =====================================================
# TELEGRAM BOT
# =====================================================

keyboard = ReplyKeyboardMarkup(
    [["🔥 Pedir estadísticas"]],
    resize_keyboard=True
)
