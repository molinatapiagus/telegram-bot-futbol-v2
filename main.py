import os
import time
import threading
import requests
from datetime import datetime
import pytz
from flask import Flask

# =====================================================
# CONFIG
# =====================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
ZONA_CO = pytz.timezone("America/Bogota")

# historial en memoria (NO rompe nada)
HISTORIAL = []

# =====================================================
# FLASK KEEP ALIVE
# =====================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot activo y estable"

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =====================================================
# TELEGRAM HELPERS
# =====================================================

def enviar_mensaje(texto, botones=None):

    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML"
    }

    if botones:
        payload["reply_markup"] = botones

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


def teclado_principal():
    return {
        "inline_keyboard": [
            [{"text": "🔥 Pedir análisis VIP", "callback_data": "VIP"}],
            [{"text": "📊 Ver historial", "callback_data": "HIST"}]
        ]
    }


# =====================================================
# LÓGICA VIP (MISMA + historial)
# =====================================================

def generar_analisis_vip():

    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    opciones = [
        {"mercado": "Más de 2.5 goles", "prob": "72%", "fundamento": "Alta frecuencia ofensiva."},
        {"mercado": "Menos de 2.5 goles", "prob": "68%", "fundamento": "Partidos cerrados."},
        {"mercado": "Gol en primer tiempo", "prob": "75%", "fundamento": "Inicio intenso con llegadas tempranas."}
    ]

    elegido = max(opciones, key=lambda x: int(x["prob"].replace("%","")))

    mensaje = f"""
🔥 <b>ANÁLISIS VIP DE FÚTBOL</b>

🕒 <b>Hora:</b> {ahora}
⚽ <b>Pronóstico:</b> {elegido['mercado']}
📊 <b>Probabilidad:</b> {elegido['prob']}

📌 {elegido['fundamento']}
"""

    # guardar historial (máx 5)
    HISTORIAL.insert(0, mensaje)
    if len(HISTORIAL) > 5:
        HISTORIAL.pop()

    return mensaje


def obtener_historial():
    if not HISTORIAL:
        return "Aún no hay análisis generados."

    texto = "📊 <b>Últimos análisis:</b>\n\n"
    for i, h in enumerate(HISTORIAL, 1):
        texto += f"{i}. {h}\n\n"

    return texto


# =====================================================
# POLLING LOOP
# =====================================================

def iniciar_bot():

    enviar_mensaje(
        "🤖 <b>Bot activo y estable</b>\n\nSelecciona una opción:",
        teclado_principal()
    )

    offset = None

    while True:
        try:
            r = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"timeout": 100, "offset": offset}
            ).json()

            for update in r.get("result", []):

                offset = update["update_id"] + 1

                # --------------------------
                # BOTONES
                # --------------------------
                if "callback_query" in update:
                    data = update["callback_query"]["data"]

                    if data == "VIP":
                        enviar_mensaje(generar_analisis_vip(), teclado_principal())

                    elif data == "HIST":
                        enviar_mensaje(obtener_historial(), teclado_principal())

                # --------------------------
                # COMANDOS TEXTO
                # --------------------------
                if "message" in update:

                    texto = update["message"].get("text", "")

                    if texto == "/start":
                        enviar_mensaje(
                            "👋 Bienvenido\n\nPulsa un botón:",
                            teclado_principal()
                        )

                    elif texto == "/ping":
                        enviar_mensaje("✅ Bot online y estable")

        except Exception as e:
            print("Error:", e)

        time.sleep(2)


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    iniciar_bot() 

