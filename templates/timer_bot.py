"""Timer Bot Template - countdown timers."""
INFO = {"name": "Timer Bot", "emoji": "⏱️", "description": "Countdown timers with alerts"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import re
async def _done(c: ContextTypes.DEFAULT_TYPE):
    await c.bot.send_message(c.job.chat_id, "⏱️ TIME'S UP! 🔔")
async def _tick(c: ContextTypes.DEFAULT_TYPE):
    left = c.job.data["left"] - 1
    c.job.data["left"] = left
    if left in (10, 30, 60):
        await c.bot.send_message(c.job.chat_id, f"⏱️ {left}s left!")
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("⏱️ Timer Bot\n\n/timer 5m\n/timer 30s\n/timer 1h")
    async def timer(u: Update, c: ContextTypes.DEFAULT_TYPE):
        m = re.match(r"/timer\s+(\d+)([smh])", u.message.text)
        if not m:
            await u.message.reply_text("❌ /timer 5m")
            return
        n, unit = int(m[1]), m[2]
        secs = n * {"s": 1, "m": 60, "h": 3600}[unit]
        c.job_queue.run_once(_done, secs, chat_id=u.effective_chat.id)
        c.job_queue.run_repeating(_tick, 1, chat_id=u.effective_chat.id, data={"left": secs})
        await u.message.reply_text(f"⏱️ Timer started: {n}{unit}")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("timer", timer))
    app.run_polling()
