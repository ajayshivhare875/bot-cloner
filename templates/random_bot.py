"""Random Generator Bot Template - dice, coin, numbers, passwords."""
INFO = {"name": "Random Bot", "emoji": "🎲", "description": "Dice, coin flip, random numbers, passwords"}

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random, secrets, string
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Dice", callback_data="dice"),
             InlineKeyboardButton("🪙 Coin", callback_data="coin")],
            [InlineKeyboardButton("🔢 Number", callback_data="num"),
             InlineKeyboardButton("🔑 Password", callback_data="pwd")]])
        await u.message.reply_text("🎲 Random Bot", reply_markup=kb)
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query; await q.answer()
        if q.data == "dice":
            await q.edit_message_text(f"🎲 You rolled: {random.randint(1, 6)}")
        elif q.data == "coin":
            await q.edit_message_text(f"🪙 {random.choice(['Heads!', 'Tails!'])}")
        elif q.data == "num":
            await q.edit_message_text(f"🔢 Random: {random.randint(1, 100)}")
        elif q.data == "pwd":
            p = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            await q.edit_message_text(f"🔑 Password: `{p}`", parse_mode="Markdown")
        await start(u, c)
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
