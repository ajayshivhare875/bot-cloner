"""UPI Payment Bot Template - collect payments via UPI QR."""
INFO = {"name": "UPI Payment Bot", "emoji": "💸", "description": "Collect UPI payments with QR codes"}

import os, urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

UPI_ID = os.environ.get("CLONE_UPI", "your-upi@bank")
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("💸 UPI Payment Bot\n\nSend an amount (e.g. 99) to generate a payment QR!")
    async def amt(u: Update, c: ContextTypes.DEFAULT_TYPE):
        try:
            a = float(u.message.text.strip())
            assert 0 < a <= 100000
        except Exception:
            await u.message.reply_text("❌ Send a valid amount (1-100000)")
            return
        params = urllib.parse.urlencode({"pa": UPI_ID, "pn": "Merchant", "am": f"{a:.2f}", "cu": "INR"})
        link = f"upi://pay?{params}"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link)}"
        await u.message.reply_photo(qr, caption=f"💰 Pay ₹{a:.2f}\n\nUPI ID: `{UPI_ID}`\n\nAfter paying, send /paid", parse_mode="Markdown")
    async def paid(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("✅ Thanks! Your payment will be verified shortly.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("paid", paid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, amt))
    app.run_polling()
