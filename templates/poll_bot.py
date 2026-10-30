"""Poll Bot Template - create voting polls."""
INFO = {"name": "Poll Bot", "emoji": "📊", "description": "Create polls and votes"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("📊 Poll Bot\n\n/poll Question | Option1 | Option2 | Option3\n\nExample:\n/poll Best color? | Red | Blue | Green")
    async def poll(u: Update, c: ContextTypes.DEFAULT_TYPE):
        txt = u.message.text[len("/poll"):].strip()
        parts = [p.strip() for p in txt.split("|")]
        if len(parts) < 3:
            await u.message.reply_text("❌ Format: /poll Question | Opt1 | Opt2")
            return
        await c.bot.send_poll(u.effective_chat.id, parts[0], parts[1:])
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("poll", poll))
    app.run_polling()
