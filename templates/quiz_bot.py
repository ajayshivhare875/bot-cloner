"""Quiz Bot Template - fun quiz game."""
INFO = {"name": "Quiz Bot", "emoji": "🧠", "description": "Quiz game with score tracking"}

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random
QS = [
    ("Capital of India?", ["Mumbai", "Delhi", "Kolkata"], 1),
    ("2 + 2 × 2 = ?", ["6", "8", "4"], 0),
    ("Largest planet?", ["Earth", "Jupiter", "Mars"], 1),
    ("Python is a ___?", ["Snake", "Language", "Both"], 2),
    ("How many days in a leap year?", ["365", "366", "364"], 1),
]
SCORE = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        SCORE.setdefault(u.effective_user.id, 0)
        await ask(u, c)
    async def ask(u, c, edit=False):
        q, opts, ans = random.choice(QS)
        c.user_data["ans"] = ans
        kb = [[InlineKeyboardButton(o, callback_data=f"q:{i}")] for i, o in enumerate(opts)]
        txt = f"🧠 {q}"
        if edit:
            await u.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await u.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query; await q.answer()
        pick = int(q.data[2:]); uid = u.effective_user.id
        if pick == c.user_data.get("ans"):
            SCORE[uid] = SCORE.get(uid, 0) + 1
            await q.edit_message_text(f"✅ Correct! Score: {SCORE[uid]}")
        else:
            await q.edit_message_text(f"❌ Wrong! Score: {SCORE.get(uid, 0)}")
        await ask(u, c, edit=False)
    async def score(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text(f"🏆 Your score: {SCORE.get(u.effective_user.id, 0)}")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
