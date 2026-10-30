"""Notes Bot Template - personal notes."""
INFO = {"name": "Notes Bot", "emoji": "📝", "description": "Save and manage personal notes"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
NOTES = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("📝 Notes Bot\n\n/add Buy milk\n/list\n/del 1\n/clear")
    async def add(u: Update, c: ContextTypes.DEFAULT_TYPE):
        t = u.message.text[len("/add"):].strip()
        if not t:
            await u.message.reply_text("❌ /add Your note")
            return
        NOTES.setdefault(u.effective_user.id, []).append(t)
        await u.message.reply_text("✅ Note added!")
    async def lst(u: Update, c: ContextTypes.DEFAULT_TYPE):
        ns = NOTES.get(u.effective_user.id, [])
        txt = "\n".join(f"{i+1}. {n}" for i, n in enumerate(ns)) or "Empty!"
        await u.message.reply_text(f"📝 Your notes:\n{txt}")
    async def delete(u: Update, c: ContextTypes.DEFAULT_TYPE):
        try:
            i = int(u.message.text.split()[1]) - 1
            NOTES[u.effective_user.id].pop(i)
            await u.message.reply_text("🗑️ Deleted!")
        except Exception:
            await u.message.reply_text("❌ /del <number>")
    async def clear(u: Update, c: ContextTypes.DEFAULT_TYPE):
        NOTES[u.effective_user.id] = []
        await u.message.reply_text("🗑️ All cleared!")
    app = Application.builder().token(token).build()
    for cmd, fn in [("start", start), ("add", add), ("list", lst), ("del", delete), ("clear", clear)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.run_polling()
