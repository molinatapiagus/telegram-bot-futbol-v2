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
# CONFIGURACIÓN (IGUAL QUE ANTES)
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

ZONA_CO = pytz.timezone("America/Bogota")


# =========================================
# SOLO LÓGICA (ÚNICO LUGAR MODIFICADO)
# =========================================

def generar_analisis():
    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    try:
        url = "https://v3.football.api-sports.io/predictions"

        headers = {
            "x-apisports-key": API_KEY
        }

        params = {
            "league": 39,   # Premier League (puedes cambiar luego)
            "season": 2026
        }

        r = requests.get(url, headers=headers, params=params, timeout=15)
        data = r.json()

        partidos = data.get("response", [])

        if not partidos:
            return "No hay partidos disponibles hoy."

        mejor = None
        mejor_prob = 0

        for p in partidos:
            home = p["teams"]["home"]["name"]
            away = p["teams"]["away"]["name"]

            porcentajes = p["predictions"]["percent"]

            for mercado, valor in porcentajes.items():
                prob = int(valor.replace("%", ""))

                if prob > mejor_prob:
                    mejor_prob = prob
                    mejor = (home, away, mercado, valor)

        home, away, mercado, valor = mejor

        return f"""
🔥 <b>ANÁLISIS VIP – FÚTBOL</b>

🏆 Partido: {home} vs {away}
🕒 Hora (Colombia): {ahora}

📊 Mercado con mayor probabilidad:
👉 <b>{mercado}</b>

📈 Probabilidad estimada: <b>{valor}</b>

Datos obtenidos desde API oficial.
"""

    except Exception:
        return "Error consultando la API. Intenta nuevamente."


# =========================================
# HANDLERS (NO TOCADOS)
# =========================================

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


# =========================================
# ARQUITECTURA (INTOCABLE Y ORIGINAL)
# =========================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot iniciado en polling puro (estable)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

