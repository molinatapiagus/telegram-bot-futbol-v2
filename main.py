import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")


# =========================
# TECLADO
# =========================
def teclado():
    keyboard = [
        [InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot activo y estable\n\nPulsa el botón para pedir análisis.",
        reply_markup=teclado()
    )


# =========================
# BOTÓN VIP
# =========================
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mensaje = (
        "🔥 ANÁLISIS VIP\n\n"
        "⚽ Pronóstico: Más de 2.5 goles\n"
        "📊 Probabilidad: 72%\n"
        "📌 Fundamentación: Alta presión ofensiva y defensas débiles\n\n"
        "Pulsa nuevamente para otro análisis 👇"
    )

    await query.message.reply_text(mensaje, reply_markup=teclado())


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip))

    print("Bot iniciado en polling estable")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
