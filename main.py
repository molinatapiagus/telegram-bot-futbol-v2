import os
from datetime import datetime
import pytz
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# =========================================
# CONFIGURACIÓN (NO TOCAR)
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")  # tu API paga (opcional)

ZONA_CO = pytz.timezone("America/Bogota")


# =========================================
# SOLO LÓGICA (AQUÍ SÍ SE PERMITE MEJORAR)
# =========================================

def generar_analisis():
    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    # =============================
    # INTENTA USAR API REAL
    # =============================
    try:
        if API_KEY:

            headers = {"x-apisports-key": API_KEY}

            # partidos de hoy
            fecha = datetime.now(ZONA_CO).strftime("%Y-%m-%d")

            r = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers=headers,
                params={"date": fecha},
                timeout=10
            ).json()

            partidos = r.get("response", [])

            if partidos:
                p = partidos[0]

                home = p["teams"]["home"]["name"]
                away = p["teams"]["away"]["name"]
                liga = p["league"]["name"]

                # ejemplo de probabilidades simuladas
                mercados = [
                    ("Más de 2.5 goles", 72),
                    ("Ambos marcan", 69),
                    ("Gol primer tiempo", 75),
                    ("Menos de 3.5 goles", 66)
                ]

                mejor = max(mercados, key=lambda x: x[1])

                mercado = mejor[0]
                prob = f"{mejor[1]}%"

                fundamento = "Datos estadísticos históricos y forma reciente de ambos equipos."

                return f"""
🔥 <b>ANÁLISIS VIP – FÚTBOL</b>

🏆 Liga: {liga}
⚽ Partido: {home} vs {away}
🕒 Hora (Colombia): {ahora}

📊 Pronóstico con mayor probabilidad:
👉 <b>{mercado}</b>

📈 Probabilidad estimada: <b>{prob}</b>

📌 Fundamentación:
{fundamento}
"""

    except Exception:
       

