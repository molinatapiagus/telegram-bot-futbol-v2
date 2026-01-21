import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIGURACIÓN BASE
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no está definido")

# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot activo y estable.\nEste es el punto base. No se toca."
    )

# =========================
# MAIN (ÚNICO ENTRY POINT)
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot iniciado en modo polling (estable)")
    app.run_polling()

if __name__ == "__main__":
    main()
