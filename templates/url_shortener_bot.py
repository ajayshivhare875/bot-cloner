"""URL Shortener Bot Template."""
INFO = {"name": "URL Shortener Bot", "emoji": "🔗", "description": "Shorten long URLs instantly"}

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re, urllib.parse
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🔗 Send me any long URL and I'll shorten it!")
    async def short(u: Update, c: ContextTypes.DEFAULT_TYPE):
        txt = u.message.text.strip()
        m = re.search(r"https?://\S+", txt)
        if not m:
            await u.message.reply_text("❌ Send a valid URL!")
            return
        import requests
        try:
            r = requests.get(f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(m.group(0))}", timeout=10)
            await u.message.reply_text(f"🔗 Short URL:\n{r.text}")
        except Exception:
            await u.message.reply_text("⚠️ Failed to shorten.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, short))
    app.run_polling()
