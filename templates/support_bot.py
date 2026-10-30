"""Support Ticket Bot Template - support ticket system."""
INFO = {"name": "Support Bot", "emoji": "🎫", "description": "Support tickets with admin panel"}

import os, json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
OWNER = os.environ.get("CLONE_OWNER", "")
TICKETS = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎫 New Ticket", callback_data="new")]])
        await u.message.reply_text("🎫 Support Bot\n\nNeed help? Open a ticket!", reply_markup=kb)
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query; await q.answer()
        if q.data == "new":
            c.user_data["ticket"] = True
            await q.edit_message_text("✍️ Describe your issue:")
        elif q.data.startswith("close:"):
            tid = q.data[6:]
            TICKETS.pop(tid, None)
            await q.edit_message_text("✅ Ticket closed!")
    async def msg(u: Update, c: ContextTypes.DEFAULT_TYPE):
        if not c.user_data.pop("ticket", False):
            return
        tid = f"T{len(TICKETS)+1}"
        TICKETS[tid] = {"user": u.effective_user.id, "text": u.message.text}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data=f"close:{tid}")]])
        if OWNER:
            try:
                await c.bot.send_message(OWNER, f"🎫 {tid} from {u.effective_user.first_name}:\n{u.message.text}", reply_markup=kb)
            except Exception:
                pass
        await u.message.reply_text(f"✅ Ticket {tid} created! We'll reply soon.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.run_polling()
