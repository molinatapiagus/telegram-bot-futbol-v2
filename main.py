from telegram.ext import Application, CommandHandler
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")


# ✅ PTB v20+ requiere async
async def start(update, context):
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
