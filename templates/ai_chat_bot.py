"""AI Chat Bot Template - chat with AI via free API."""
INFO = {"name": "AI Chat Bot", "emoji": "🤖", "description": "Chat with AI (uses free Groq API key)"}

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

GROQ_KEY = os.environ.get("CLONE_GROQ_KEY", "")
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🤖 AI Chat Bot\n\nJust send me any message and I'll reply!")
    async def chat(u: Update, c: ContextTypes.DEFAULT_TYPE):
        if not GROQ_KEY:
            await u.message.reply_text("⚠️ AI not configured. Owner: set CLONE_GROQ_KEY env.")
            return
        await c.bot.send_chat_action(u.effective_chat.id, "typing")
        import requests
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                json={"model": "llama-3.1-8b-instant",
                      "messages": [{"role": "user", "content": u.message.text}]},
                timeout=30)
            txt = r.json()["choices"][0]["message"]["content"]
            await u.message.reply_text(txt[:4000])
        except Exception as e:
            await u.message.reply_text(f"⚠️ Error: {type(e).__name__}")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
