"""File Store Bot Template - save files and get share links."""
INFO = {"name": "File Store Bot", "emoji": "📁", "description": "Store files, get download info"}

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
FILES = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("📁 Send me any file/photo/video and I'll store it!\nUse /myfiles to list.")
    async def save(u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        f = u.message.document or u.message.photo or u.message.video or u.message.audio
        if not f:
            return
        fid = f.file_id if not isinstance(f, list) else f[-1].file_id
        FILES.setdefault(uid, []).append(fid)
        await u.message.reply_text(f"✅ Saved! Total files: {len(FILES[uid])}")
    async def myfiles(u: Update, c: ContextTypes.DEFAULT_TYPE):
        fs = FILES.get(u.effective_user.id, [])
        await u.message.reply_text(f"📁 You have {len(fs)} files stored." if fs else "Empty!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myfiles", myfiles))
    app.add_handler(MessageHandler((filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO) & ~filters.COMMAND, save))
    app.run_polling()
