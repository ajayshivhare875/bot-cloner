"""Reminder Bot Template - set reminders."""
INFO = {"name": "Reminder Bot", "emoji": "⏰", "description": "Set reminders, bot pings you later"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import re
async def _fire(c: ContextTypes.DEFAULT_TYPE):
    await c.bot.send_message(c.job.chat_id, f"⏰ Reminder: {c.job.data}")
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("⏰ Reminder Bot\n\n/remind 10m Drink water\n/remind 1h Meeting\n\nUnits: s, m, h")
    async def remind(u: Update, c: ContextTypes.DEFAULT_TYPE):
        m = re.match(r"/remind\s+(\d+)([smh])\s+(.+)", u.message.text)
        if not m:
            await u.message.reply_text("❌ Format: /remind 10m Your message")
            return
        n, unit, msg = int(m[1]), m[2], m[3]
        secs = n * {"s": 1, "m": 60, "h": 3600}[unit]
        c.job_queue.run_once(_fire, secs, chat_id=u.effective_chat.id, data=msg)
        await u.message.reply_text(f"✅ Reminder set for {n}{unit}!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind))
    app.run_polling()
