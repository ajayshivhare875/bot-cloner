"""Referral Bot Template - referral system with points and leaderboard."""
INFO = {"name": "Referral Bot", "emoji": "👥", "description": "Referral system with points, leaderboard and rewards"}

import json, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

DATA = {}
def _load(tid):
    p = f"/tmp/ref_{tid}.json"
    try:
        return json.load(open(p))
    except Exception:
        return {"users": {}}
def _save(tid, d):
    json.dump(d, open(f"/tmp/ref_{tid}.json", "w"))

def run(token):
    OWNER = os.environ.get("CLONE_OWNER", "")
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        tid = str(u.effective_chat.id)
        d = _load(tid); uid = str(u.effective_user.id)
        ref = c.args[0] if c.args else None
        if uid not in d["users"]:
            d["users"][uid] = {"pts": 10, "refs": 0, "name": u.effective_user.first_name}
            if ref and ref != uid and ref in d["users"]:
                d["users"][ref]["pts"] += 50; d["users"][ref]["refs"] += 1
            _save(tid, d)
            await u.message.reply_text(f"🎉 Welcome! +10 bonus points!")
        me = await c.bot.get_me()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 My Points", callback_data="pts")],
            [InlineKeyboardButton("👥 Refer & Earn", callback_data="ref")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="lb")]])
        await u.message.reply_text(f"👥 Referral Bot\nShare your link, earn 50 pts per referral!", reply_markup=kb)
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query; await q.answer()
        tid = str(u.effective_chat.id); d = _load(tid); uid = str(u.effective_user.id)
        usr = d["users"].get(uid, {"pts": 0, "refs": 0})
        me = await c.bot.get_me()
        if q.data == "pts":
            await q.edit_message_text(f"💰 Points: {usr['pts']}\n👥 Referrals: {usr['refs']}")
        elif q.data == "ref":
            await q.edit_message_text(f"🔗 Your link:\nhttps://t.me/{me.username}?start={uid}\n\n+50 pts per friend!")
        elif q.data == "lb":
            top = sorted(d["users"].items(), key=lambda x: -x[1]["pts"])[:10]
            txt = "🏆 Leaderboard:\n" + "\n".join(f"{i+1}. {v.get('name','?')} - {v['pts']} pts" for i, (k, v) in enumerate(top))
            await q.edit_message_text(txt or "Empty!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
