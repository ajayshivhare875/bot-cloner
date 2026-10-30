"""Translator Bot Template - translate text free."""
INFO = {"name": "Translator Bot", "emoji": "🌐", "description": "Translate text between languages"}

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
LANG = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🌐 Translator Bot\n\n/lang hi (set target language)\nThen just send any text!\n\nCodes: hi, es, fr, de, ar, bn, ta, te")
    async def lang(u: Update, c: ContextTypes.DEFAULT_TYPE):
        l = u.message.text[len("/lang"):].strip().lower() or "hi"
        LANG[u.effective_user.id] = l
        await u.message.reply_text(f"✅ Target language: {l}")
    async def tr(u: Update, c: ContextTypes.DEFAULT_TYPE):
        import requests, urllib.parse
        tgt = LANG.get(u.effective_user.id, "hi")
        try:
            q = urllib.parse.quote(u.message.text)
            r = requests.get(f"https://api.mymemory.translated.net/get?q={q}&langpair=en|{tgt}", timeout=10).json()
            await u.message.reply_text(f"🌐 ({tgt}):\n{r['responseData']['translatedText']}")
        except Exception:
            await u.message.reply_text("⚠️ Translation failed.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tr))
    app.run_polling()
