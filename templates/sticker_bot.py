"""Sticker Maker Bot Template - images to stickers."""
INFO = {"name": "Sticker Maker Bot", "emoji": "🎨", "description": "Convert photos to stickers"}

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🎨 Sticker Maker\n\nSend me any photo and I'll convert it to a sticker!")
    async def mk(u: Update, c: ContextTypes.DEFAULT_TYPE):
        photo = u.message.photo[-1]
        f = await photo.get_file()
        await u.message.reply_sticker(sticker=f.file_id)
        await u.message.reply_text("✅ Done! Long-press to add to favorites.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, mk))
    app.run_polling()
