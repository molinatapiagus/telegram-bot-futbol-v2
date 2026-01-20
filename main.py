import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# CONFIGURACIÓN BASE (NO TOCAR)
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no está definido en las variables de entorno")

# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot activo y estable.\nEste es el punto base. No se toca."
    )

# =========================
# MAIN
# =========================

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    print("🤖 Bot iniciado en modo polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
