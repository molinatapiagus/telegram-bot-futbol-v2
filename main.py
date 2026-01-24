import os
import time
import requests
from datetime import datetime
import pytz

# ===============================
# VARIABLES (Render ENV)
# ===============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ZONA_CO = pytz.timezone("America/Bogota")


# ===============================
# TELEGRAM HELPERS
# ===============================
def enviar_mensaje(texto, botones=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML"
    }

    if botones:
        payload["reply_markup"] = botones

    requests.post(url, json=payload)


def teclado_vip():
    return {
        "keyboard": [["🔥 Pedir análisis VIP"]],
        "resize_keyboard": True
    }


# ===============================
# GENERADOR ANÁLISIS (EL QUE YA FUNCIONABA)
# ===============================
def generar_analisis():
    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    return f"""
🔥 <b>ANÁLISIS VIP DE FÚTBOL</b>

🕒 Hora (Colombia): {ahora}

⚽ Pronóstico:
👉 Gol en primer tiempo

📊 Probabilidad estimada: 75%

📌 Fundamentación:
Inicio intenso con llegadas tempranas.
"""


# ===============================
# POLLING PURO (ESTABLE)
# ===============================
def iniciar_bot():
    offset = None

    enviar_mensaje(
        "🤖 <b>Bot activo y estable</b>\nPulsa el botón para pedir análisis.",
        teclado_vip()
    )

    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"timeout": 100, "offset": offset}
            ).json()

            for update in r["result"]:
                offset = update["update_id"] + 1

                if "message" in update:
                    texto = update["message"].get("text", "")

                    if texto == "🔥 Pedir análisis VIP":
                        enviar_mensaje(generar_analisis(), teclado_vip())

        except Exception as e:
            print("Error:", e)

        time.sleep(2)


# ===============================
# MAIN (SIN FLASK, SIN HILOS)
# ===============================
if __name__ == "__main__":
    iniciar_bot()

