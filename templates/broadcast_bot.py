"""Broadcast Bot Template - broadcast messages to subscribers."""
INFO = {"name": "Broadcast Bot", "emoji": "📢", "description": "Subscribe and receive broadcasts"}

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
OWNER = os.environ.get("CLONE_OWNER", "")
SUBS = set()
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        SUBS.add(u.effective_user.id)
        await u.message.reply_text("📢 Subscribed! You'll receive broadcasts.")
    async def bc(u: Update, c: ContextTypes.DEFAULT_TYPE):
        if str(u.effective_user.id) != str(OWNER):
            await u.message.reply_text("❌ Admin only!")
            return
        msg = u.message.text[len("/broadcast"):].strip()
        if not msg:
            await u.message.reply_text("❌ /broadcast Your message")
            return
        ok = 0
        for sid in SUBS:
            try:
                await c.bot.send_message(sid, f"📢 {msg}")
                ok += 1
            except Exception:
                pass
        await u.message.reply_text(f"✅ Sent to {ok} subscribers!")
    async def subs(u: Update, c: ContextTypes.DEFAULT_TYPE):
        if str(u.effective_user.id) != str(OWNER):
            return
        await u.message.reply_text(f"👥 Subscribers: {len(SUBS)}")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", bc))
    app.add_handler(CommandHandler("subs", subs))
    app.run_polling()
