import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")


# ===============================
# /start
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🔥 Pedir análisis VIP", callback_data="vip")]
    ]

    # 🔴 BORRA cualquier teclado viejo persistente
    await update.message.reply_text(
        "🤖 Bot activo y estable\n\nPulsa el botón para pedir análisis:",
        reply_markup=ReplyKeyboardRemove()
    )

    # ✅ SOLO inline button (correcto)
    await update.message.reply_text(
        "Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===============================
# Botón VIP
# ===============================
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📊 Análisis VIP generado correctamente\n\n( aquí luego conectamos tu lógica real )"
    )


# ===============================
# MAIN (polling puro estable)
# ===============================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    print("Bot iniciado en polling puro (estable)")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()
