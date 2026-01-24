import os
from datetime import datetime
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ZONA_CO = pytz.timezone("America/Bogota")


# ==============================
# SOLO LÓGICA (FUNCIONES)
# ==============================

def generar_analisis():
    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    opciones = [
        ("Más de 2.5 goles", "72%", "Alta presión ofensiva y defensas vulnerables."),
        ("Menos de 2.5 goles", "68%", "Partido cerrado y ritmo conservador."),
        ("Gol en primer tiempo", "75%", "Inicio intenso con llegadas tempranas.")
    ]

    mercado, prob, fundamento = max(
        opciones,
        key=lambda x: int(x[1].replace("%", ""))
    )

    return f"""
🔥 <b>ANÁLISIS VIP DE FÚTBOL</b>

🕒 Hora (Colombia): {ahora}

⚽ Pronóstico:
👉 <b>{mercado}</b>

📊 Probabilidad estimada: <b>{prob}</b>

📌 Fundamentación:
{fundamento}
"""


# ==============================
# HANDLERS (NO TOCAR)
# ==============================

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


# ==============================
# ARQUITECTURA (PROHIBIDO TOCAR)
# ==============================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot iniciado en polling puro (estable)")
    app.run_polling(drop_pending_updates=True)


if name == "main":
    main()

