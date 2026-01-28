import os
import requests
import math
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN_BOT = os.getenv("BOT_TOKEN")
TOKEN_FOOTBALL = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": TOKEN_FOOTBALL}


# ======================================================
# POISSON
# ======================================================

def poisson(l, k):
    return (l ** k * math.exp(-l)) / math.factorial(k)


def probs(lh, la):
    over = home = btts = 0

    for i in range(6):
        for j in range(6):
            p = poisson(lh, i) * poisson(la, j)

            if i + j > 2:
                over += p
            if i > j:
                home += p
            if i > 0 and j > 0:
                btts += p

    return over, home, btts


# ======================================================
# HISTÓRICO
# ======================================================

def stats(team_id):
    r = requests.get(
        f"{BASE_URL}/teams/{team_id}/matches?limit=15&status=FINISHED",
        headers=HEADERS
    )

    if r.status_code != 200:
        return 1.3, 1.3

    matches = r.json()["matches"]

    gf = gc = 0

    for m in matches:
        if m["homeTeam"]["id"] == team_id:
            gf += m["score"]["fullTime"]["home"] or 0
            gc += m["score"]["fullTime"]["away"] or 0
        else:
            gf += m["score"]["fullTime"]["away"] or 0
            gc += m["score"]["fullTime"]["home"] or 0

    n = len(matches) or 1

    return gf/n, gc/n


# ======================================================
# PARTIDOS PROGRAMADOS
# ======================================================

def partidos():

    r = requests.get(
        f"{BASE_URL}/matches?status=SCHEDULED",
        headers=HEADERS
    )

    hoy = datetime.utcnow().date()

    lista = []

    for m in r.json()["matches"]:
        fecha = datetime.fromisoformat(m["utcDate"].replace("Z", "")).date()

        if abs((fecha - hoy).days) <= 2:
            lista.append(m)

    return lista[:5]


# ======================================================
# FORMATO PROFESIONAL
# ======================================================

def analizar():

    resultados = []

    for g in partidos():

        home = g["homeTeam"]["name"]
        away = g["awayTeam"]["name"]

        hgf, hgc = stats(g["homeTeam"]["id"])
        agf, agc = stats(g["awayTeam"]["id"])

        lh = (hgf + agc) / 2
        la = (agf + hgc) / 2

        over, homep, btts = probs(lh, la)

        opciones = {
            "Over 2.5 goles": over,
            "Ambos marcan (BTTS)": btts,
            "Gana local": homep
        }

        mercado = max(opciones, key=opciones.get)
        prob = opciones[mercado]

        if prob < 0.60:
            continue

        hora = datetime.fromisoformat(g["utcDate"].replace("Z","")).strftime("%H:%M")

        mensaje = f"""
🔥 <b>ANÁLISIS VIP AVANZADO – FÚTBOL</b>

🏆 <b>Partido:</b> {home} vs {away}
🕒 <b>Hora:</b> {hora}

📊 <b>ESCENARIO CON MAYOR PROBABILIDAD</b>
👉 {mercado}

📈 <b>Probabilidad matemática:</b> {round(prob*100)}%

🧠 <b>Diagnóstico:</b>
• Promedio goles local: {round(hgf,2)}
• Promedio goles visita: {round(agf,2)}
• Proyección goles esperados: {round(lh+la,2)}
• Modelo Poisson + histórico reciente

━━━━━━━━━━━━━━━━━━
"""

        resultados.append(mensaje)

    if not resultados:
        return "⚠️ No hay picks con valor estadístico fuerte hoy."

    return "\n".join(resultados)


# ======================================================
# TELEGRAM
# ======================================================

def teclado():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Pedir estadísticas", callback_data="vip")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo", reply_markup=teclado())


async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(analizar(), parse_mode="HTML", reply_markup=teclado())


# ======================================================
# MAIN
# ======================================================

def main():
    app = Application.builder().token(TOKEN_BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vip, pattern="vip"))

    app.run_polling()


if __name__ == "__main__":
    main()
