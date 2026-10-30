"""Bot Cloner - main control bot. Browse 20 templates, clone with your token."""
import os
from dotenv import load_dotenv
load_dotenv()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import manager

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN required")

PER_PAGE = 8

def _tpl_kb(page=0):
    tpls = manager.list_templates()
    names = sorted(tpls.keys())
    start = page * PER_PAGE
    kb = []
    for n in names[start:start + PER_PAGE]:
        info = tpls[n]
        kb.append([InlineKeyboardButton(f"{info.get('emoji','🤖')} {info.get('name',n)}", callback_data=f"tpl:{n}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("« Prev", callback_data=f"page:{page-1}"))
    if start + PER_PAGE < len(names):
        nav.append(InlineKeyboardButton("Next »", callback_data=f"page:{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("🤖 My Bots", callback_data="mybots")])
    return InlineKeyboardMarkup(kb), len(names)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    kb, n = _tpl_kb(0)
    await u.message.reply_text(
        f"🏭 **Bot Cloner Factory**\n\nChoose from {n} bot templates!\n\n1️⃣ Pick a template\n2️⃣ Send your bot token (from @BotFather)\n3️⃣ Your bot goes LIVE instantly! 🚀",
        reply_markup=kb, parse_mode="Markdown")

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    d = q.data
    if d.startswith("page:"):
        kb, _ = _tpl_kb(int(d[5:]))
        await q.edit_message_text("🏭 **Bot Cloner Factory**\n\nPick a template:", reply_markup=kb, parse_mode="Markdown")
    elif d.startswith("tpl:"):
        name = d[4:]
        info = manager.list_templates().get(name, {})
        c.user_data["clone_tpl"] = name
        await q.edit_message_text(
            f"{info.get('emoji','🤖')} **{info.get('name',name)}**\n\n{info.get('description','')}\n\n📝 Now send your bot token (from @BotFather → /newbot):",
            parse_mode="Markdown")
    elif d == "mybots":
        bots = manager.my_bots(u.effective_user.id)
        if not bots:
            await q.edit_message_text("🤖 No cloned bots yet!")
            return
        kb = []
        for iid, b in bots.items():
            st = "🟢" if b.get("alive") else "🔴"
            kb.append([InlineKeyboardButton(f"{st} {b['template']}", callback_data=f"manage:{iid}")])
        kb.append([InlineKeyboardButton("« Back", callback_data="page:0")])
        await q.edit_message_text("🤖 **My Bots:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif d.startswith("manage:"):
        iid = d[7:]
        bots = manager.my_bots(u.effective_user.id)
        b = bots.get(iid)
        if not b:
            await q.edit_message_text("Not found!")
            return
        st = "🟢 Running" if b.get("alive") else "🔴 Stopped"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop", callback_data=f"stop:{iid}")],
            [InlineKeyboardButton("« My Bots", callback_data="mybots")]])
        await q.edit_message_text(f"🤖 {b['template']}\nStatus: {st}\nID: `{iid}`", reply_markup=kb, parse_mode="Markdown")
    elif d.startswith("stop:"):
        ok, msg = manager.stop_bot(d[5:], u.effective_user.id)
        await q.edit_message_text(f"{'✅ Stopped!' if ok else '❌ '+msg}")

async def on_token(u: Update, c: ContextTypes.DEFAULT_TYPE):
    tpl = c.user_data.get("clone_tpl")
    if not tpl:
        return
    token = u.message.text.strip()
    # delete the token message for security
    try:
        await u.message.delete()
    except Exception:
        pass
    wait = await u.message.reply_text("⏳ Cloning your bot...")
    iid, err = manager.clone_bot(tpl, token, u.effective_user.id, u.effective_user.first_name or "")
    c.user_data.pop("clone_tpl", None)
    if err:
        await wait.edit_text(f"❌ Failed: {err}")
    else:
        info = manager.list_templates().get(tpl, {})
        await wait.edit_text(
            f"🎉 **Your bot is LIVE!**\n\n{info.get('emoji','🤖')} {info.get('name',tpl)}\n🆔 `{iid}`\n\nGo test it now! 🚀",
            parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_token))
    print("Bot Cloner running...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
