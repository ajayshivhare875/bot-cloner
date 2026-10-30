"""Crypto Price Bot Template - live crypto prices."""
INFO = {"name": "Crypto Price Bot", "emoji": "₿", "description": "Live cryptocurrency prices"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("₿ Crypto Bot\n\n/price btc\n/price eth\n/price doge")
    async def price(u: Update, c: ContextTypes.DEFAULT_TYPE):
        coin = u.message.text[len("/price"):].strip().lower() or "bitcoin"
        import requests
        try:
            r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,inr&include_24hr_change=true", timeout=10).json()
            if coin not in r:
                await u.message.reply_text("❌ Coin not found! Try: bitcoin, ethereum, dogecoin")
                return
            d = r[coin]
            chg = d.get("usd_24h_change", 0)
            emo = "🟢" if chg >= 0 else "🔴"
            await u.message.reply_text(f"{emo} {coin.upper()}\n💵 ${d['usd']:,.2f}\n₹{d['inr']:,.2f}\n24h: {chg:+.2f}%")
        except Exception:
            await u.message.reply_text("⚠️ Failed to fetch price.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.run_polling()
