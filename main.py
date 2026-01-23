from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ AHORA ES ASYNC
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot activo y estable")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot iniciado en polling puro (estable)")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message"]
    )

if __name__ == "__main__":
    main()

