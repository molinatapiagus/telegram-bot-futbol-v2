from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime
import pytz
import os

TOKEN = os.getenv("BOT_TOKEN")
ZONA_CO = pytz.timezone("America/Bogota")


# ========= MENSAJE VIP =========
def generar_analisis():
    ahora = datetime.now(ZONA_CO).strftime("%d/%m/%Y %I:%M %p")

    return f"""
🔥 ANÁLISIS VIP DE FÚTBOL

🕒 Hora (Colombia): {ahora}

⚽ Pronóstico: Más de 2.5 goles
📊 Probabilidad: 72%

Pulsa el botón para otro análisis 👇
"""


# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]
    ]

    await update.message.reply_text(
        "🤖 Bot VIP activo\nPulsa el botón:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ========= BOTÓN =========
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(generar_analisis())


# ========= MAIN =========
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
