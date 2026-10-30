"""Group Manager Bot Template - welcome + basic moderation."""
INFO = {"name": "Group Manager Bot", "emoji": "🛡️", "description": "Welcome messages and group tools"}

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🛡️ Group Manager\n\nAdd me to a group as admin!\n\n/rules - set rules\n/welcome - test welcome")
    async def welcome(u: Update, c: ContextTypes.DEFAULT_TYPE):
        for m in u.message.new_chat_members:
            await u.message.reply_text(f"👋 Welcome {m.first_name}!\nPlease read the group rules. 🎉")
    async def rules(u: Update, c: ContextTypes.DEFAULT_TYPE):
        t = u.message.text[len("/rules"):].strip()
        if t:
            c.bot_data["rules"] = t
            await u.message.reply_text("✅ Rules saved!")
        else:
            await u.message.reply_text(f"📜 Rules:\n{c.bot_data.get('rules', 'No rules set yet.')}")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("welcome", lambda u, c: u.message.reply_text("👋 Test welcome!")))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.run_polling()
