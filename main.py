from telegram.ext import Application, CommandHandler
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("Bot activo y estable")

def main():
    # 🔴 IMPORTANTE: pequeña espera para que Render mate instancias viejas
    time.sleep(5)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot iniciado en polling puro (estable)")

    app.run_polling(
        drop_pending_updates=True,
        close_loop=False,   # 🔴 clave en Render
        allowed_updates=["message"]
    )

if __name__ == "__main__":
    main()
