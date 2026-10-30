"""Feedback Bot Template - collect user feedback."""
INFO = {"name": "Feedback Bot", "emoji": "💬", "description": "Collect feedback from users"}

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
OWNER = os.environ.get("CLONE_OWNER", "")
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("💬 Feedback Bot\n\nJust send your feedback/suggestion here!")
    async def fb(u: Update, c: ContextTypes.DEFAULT_TYPE):
        if OWNER:
            try:
                await c.bot.send_message(OWNER, f"💬 New feedback from {u.effective_user.first_name}:\n\n{u.message.text}")
            except Exception:
                pass
        await u.message.reply_text("✅ Thanks for your feedback!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fb))
    app.run_polling()
