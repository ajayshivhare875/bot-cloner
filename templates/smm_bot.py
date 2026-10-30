"""SMM Panel Bot Template - social media services ordering demo."""
INFO = {"name": "SMM Panel Bot", "emoji": "📣", "description": "SMM services panel with orders and balance"}

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

SERVICES = [
    ("Instagram Followers", "1K", 80), ("Instagram Likes", "1K", 30),
    ("YouTube Views", "1K", 120), ("YouTube Subs", "1K", 400),
    ("Telegram Members", "1K", 150), ("TikTok Followers", "1K", 90),
]
BAL = {}
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        BAL.setdefault(u.effective_user.id, 500)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Services", callback_data="svc")],
            [InlineKeyboardButton("💰 Balance", callback_data="bal")],
            [InlineKeyboardButton("📦 My Orders", callback_data="ord")]])
        await u.message.reply_text("📣 SMM Panel\nBoost your social media!", reply_markup=kb)
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query; await q.answer(); uid = u.effective_user.id
        BAL.setdefault(uid, 500)
        if q.data == "svc":
            kb = [[InlineKeyboardButton(f"{n} ({q_}) - ₹{p}", callback_data=f"buy:{i}")] for i, (n, q_, p) in enumerate(SERVICES)]
            kb.append([InlineKeyboardButton("« Back", callback_data="home")])
            await q.edit_message_text("🛒 Services:", reply_markup=InlineKeyboardMarkup(kb))
        elif q.data == "bal":
            await q.edit_message_text(f"💰 Balance: ₹{BAL[uid]}")
        elif q.data == "ord":
            await q.edit_message_text("📦 No orders yet. (Demo mode)")
        elif q.data == "home":
            await start(u, c)
        elif q.data.startswith("buy:"):
            i = int(q.data[4:]); n, q_, p = SERVICES[i]
            if BAL[uid] >= p:
                BAL[uid] -= p
                await q.edit_message_text(f"✅ Order placed!\n{n} ({q_})\n💰 New balance: ₹{BAL[uid]}")
            else:
                await q.edit_message_text("❌ Insufficient balance!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
