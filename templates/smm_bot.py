"""SMM Panel Pro Template - FULL SMM reseller bot.
Features: real SMM API (services/orders/balance), live order status,
UPI deposit system with admin approval, admin panel, price list.
Owner configures API URL + key + UPI ID via /admin after cloning.
"""
INFO = {"name": "SMM Panel Pro", "emoji": "📣", "description": "FULL SMM panel: real API orders, FamBridge auto-payments, admin panel"}

import os, json, re, time, urllib.parse
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

OWNER = os.environ.get("CLONE_OWNER", "")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "smm")
os.makedirs(DATA_DIR, exist_ok=True)
SVC_CACHE = {"at": 0, "data": []}


def _db():
    p = os.path.join(DATA_DIR, f"{OWNER or 'default'}.json")
    try:
        return json.load(open(p))
    except Exception:
        return {"cfg": {}, "users": {}, "deposits": {}, "orders": {}}


def _save(d):
    p = os.path.join(DATA_DIR, f"{OWNER or 'default'}.json")
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, p)


def _bal(d, uid):
    return d["users"].get(str(uid), {}).get("balance", 0.0)


def _add_bal(d, uid, amt):
    u = d["users"].setdefault(str(uid), {"balance": 0.0})
    u["balance"] = round(u.get("balance", 0.0) + amt, 2)


def smm(cfg, action, params=None):
    url = (cfg.get("api_url") or "").rstrip("/")
    key = cfg.get("api_key") or ""
    if not url or not key:
        return None, "not_configured"
    data = {"key": key, "action": action}
    if params:
        data.update(params)
    try:
        r = requests.post(url, data=data, timeout=25)
        j = r.json()
        if isinstance(j, dict) and j.get("error"):
            return None, str(j["error"])
        return j, ""
    except Exception as e:
        return None, f"API error: {type(e).__name__}"


def get_services(d):
    cfg = d["cfg"]
    if time.time() - SVC_CACHE["at"] < 600 and SVC_CACHE["data"]:
        return SVC_CACHE["data"], ""
    j, err = smm(cfg, "services")
    if err:
        return [], err
    SVC_CACHE.update({"at": time.time(), "data": j if isinstance(j, list) else []})
    return SVC_CACHE["data"], ""


GATEWAY_URL = "https://fambridge.onrender.com"


def gb(cfg, method, path, payload=None):
    """Call FamBridge gateway API. Returns (status_code, json)."""
    base = (cfg.get("gateway_url") or GATEWAY_URL).rstrip("/")
    try:
        if method == "GET":
            r = requests.get(base + path, params=payload, timeout=20)
        else:
            r = requests.post(base + path, json=payload, timeout=20)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {}
    except Exception as e:
        return 0, {"error": type(e).__name__}


def main_menu(is_owner):
    kb = [
        [InlineKeyboardButton("🛒 New Order", callback_data="new_order"),
         InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("💳 Add Funds", callback_data="addfunds")],
        [InlineKeyboardButton("📊 Price List", callback_data="prices")],
    ]
    if is_owner:
        kb.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(kb)


def admin_menu(d):
    cfg = d["cfg"]
    pend = sum(1 for x in d["deposits"].values() if x["status"] == "pending")
    kb = [
        [InlineKeyboardButton(f"🔗 API URL: {'✅' if cfg.get('api_url') else '❌'}", callback_data="adm_url")],
        [InlineKeyboardButton(f"🔑 API Key: {'✅' if cfg.get('api_key') else '❌'}", callback_data="adm_key")],
        [InlineKeyboardButton(f"💸 UPI ID: {'✅' if cfg.get('upi') else '❌'}", callback_data="adm_upi")],
        [InlineKeyboardButton(f"🌉 FamBridge Gateway: {'✅' if cfg.get('gateway_key') else '❌'}", callback_data="adm_gw")],
        [InlineKeyboardButton("🧪 Test API", callback_data="adm_test")],
        [InlineKeyboardButton(f"💳 Deposits ({pend} pending)", callback_data="adm_deps")],
        [InlineKeyboardButton("➕ Add Balance", callback_data="adm_addbal")],
        [InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],
        [InlineKeyboardButton("« Back", callback_data="home")],
    ]
    return InlineKeyboardMarkup(kb)


def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        d = _db()
        c.user_data.clear()
        is_owner = str(uid) == str(OWNER)
        await u.message.reply_text(
            f"📣 <b>SMM Panel Pro</b>\n\n💰 Balance: ₹{_bal(d, uid):.2f}\n\nSelect an option:",
            reply_markup=main_menu(is_owner), parse_mode="HTML")

    # ---------- callback router ----------
    async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
        q = u.callback_query
        await q.answer()
        uid = u.effective_user.id
        data = q.data
        d = _db()
        is_owner = str(uid) == str(OWNER)

        if data == "home":
            c.user_data.clear()
            await q.edit_message_text(f"📣 <b>SMM Panel Pro</b>\n\n💰 Balance: ₹{_bal(d, uid):.2f}",
                                      reply_markup=main_menu(is_owner), parse_mode="HTML")

        # ----- NEW ORDER -----
        elif data == "new_order":
            svcs, err = get_services(d)
            if err == "not_configured":
                await q.edit_message_text("⚠️ SMM API not configured yet. Owner: use /admin to set it up.")
                return
            if err or not svcs:
                await q.edit_message_text(f"⚠️ Could not load services: {err}")
                return
            cats = sorted(set(s.get("category", "Other") for s in svcs))
            c.user_data["cats"] = cats
            kb = [[InlineKeyboardButton(cat[:40], callback_data=f"cat:{i}")] for i, cat in enumerate(cats[:30])]
            kb.append([InlineKeyboardButton("« Back", callback_data="home")])
            await q.edit_message_text("📂 <b>Select category:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

        elif data.startswith("cat:"):
            svcs, _ = get_services(d)
            cats = c.user_data.get("cats", [])
            try:
                cat = cats[int(data[4:])]
            except Exception:
                await q.edit_message_text("❌ Invalid category.")
                return
            items = [s for s in svcs if s.get("category") == cat][:40]
            c.user_data["items"] = items
            kb = [[InlineKeyboardButton(f"{s.get('name','?')[:35]} — ₹{s.get('rate','?')}/1k", callback_data=f"svc:{i}")] for i, s in enumerate(items)]
            kb.append([InlineKeyboardButton("« Categories", callback_data="new_order")])
            await q.edit_message_text(f"📂 <b>{cat}</b>\nSelect service:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

        elif data.startswith("svc:"):
            try:
                s = c.user_data["items"][int(data[4:])]
            except Exception:
                await q.edit_message_text("❌ Invalid service.")
                return
            c.user_data["order"] = {"stage": "link", "service": s}
            await q.edit_message_text(
                f"🛒 <b>{s.get('name')}</b>\n💵 ₹{s.get('rate')}/1000\n📦 Min: {s.get('min')} | Max: {s.get('max')}\n\n🔗 Send the <b>link</b> now:",
                parse_mode="HTML")

        elif data == "order_confirm":
            o = c.user_data.get("order", {})
            s = o.get("service", {})
            qty = o.get("qty", 0)
            charge = round(float(s.get("rate", 0)) * qty / 1000, 2)
            if _bal(d, uid) < charge:
                await q.edit_message_text(f"❌ Insufficient balance!\nNeed ₹{charge:.2f}, you have ₹{_bal(d, uid):.2f}\n\nUse 💳 Add Funds first.")
                return
            j, err = smm(d["cfg"], "add", {"service": s.get("service"), "link": o.get("link"), "quantity": qty})
            if err or not isinstance(j, dict) or not j.get("order"):
                await q.edit_message_text(f"❌ Order failed: {err or j}")
                return
            _add_bal(d, uid, -charge)
            oid = str(j["order"])
            d["orders"][oid] = {"uid": str(uid), "service": s.get("name"), "qty": qty,
                                "charge": charge, "link": o.get("link"), "at": time.time()}
            _save(d)
            c.user_data.pop("order", None)
            await q.edit_message_text(
                f"✅ <b>Order placed!</b>\n\n🆔 Order ID: <code>{oid}</code>\n📦 {s.get('name')}\n🔢 Qty: {qty}\n💵 Charged: ₹{charge:.2f}\n💰 New balance: ₹{_bal(d, uid):.2f}",
                reply_markup=main_menu(is_owner), parse_mode="HTML")

        elif data == "order_cancel":
            c.user_data.pop("order", None)
            await q.edit_message_text("❌ Order cancelled.", reply_markup=main_menu(is_owner))

        # ----- MY ORDERS -----
        elif data == "my_orders":
            mine = [(k, v) for k, v in d["orders"].items() if v["uid"] == str(uid)][-10:]
            if not mine:
                await q.edit_message_text("📦 No orders yet.", reply_markup=main_menu(is_owner))
                return
            kb = [[InlineKeyboardButton(f"🔄 {k} — {v['service'][:25]}", callback_data=f"ord:{k}")] for k, v in reversed(mine)]
            kb.append([InlineKeyboardButton("« Back", callback_data="home")])
            await q.edit_message_text("📦 <b>Your orders</b> (tap to refresh status):",
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

        elif data.startswith("ord:"):
            oid = data[4:]
            j, err = smm(d["cfg"], "status", {"order": oid})
            o = d["orders"].get(oid, {})
            if err:
                txt = f"⚠️ Status check failed: {err}"
            else:
                txt = (f"🆔 <b>{oid}</b>\n📦 {o.get('service', '?')}\n"
                       f"📊 Status: <b>{j.get('status', '?')}</b>\n"
                       f"✅ Done: {j.get('start_count', '?')} → remains {j.get('remains', '?')}")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("« My Orders", callback_data="my_orders")]])
            await q.edit_message_text(txt, reply_markup=kb, parse_mode="HTML")

        # ----- BALANCE / PRICES -----
        elif data == "balance":
            j, err = smm(d["cfg"], "balance")
            api_bal = f"\n🏦 API balance: {j.get('balance', '?')} {j.get('currency', '')}" if not err and j else ""
            await q.edit_message_text(f"💰 <b>Your balance: ₹{_bal(d, uid):.2f}</b>{api_bal}",
                                      reply_markup=main_menu(is_owner), parse_mode="HTML")

        elif data == "prices":
            svcs, err = get_services(d)
            if err == "not_configured":
                await q.edit_message_text("⚠️ SMM API not configured yet.")
                return
            lines = [f"• {s.get('name','?')[:30]} — ₹{s.get('rate')}/1k" for s in svcs[:25]]
            await q.edit_message_text("📊 <b>Price list</b> (top 25):\n\n" + "\n".join(lines),
                                      reply_markup=main_menu(is_owner), parse_mode="HTML")

        # ----- ADD FUNDS -----
        elif data == "addfunds":
            if d["cfg"].get("gateway_key"):
                c.user_data["deposit"] = {"stage": "amount", "via": "gateway"}
                await q.edit_message_text("💳 <b>Add Funds</b> 🌉\n<i>Auto-verified via FamBridge — no waiting!</i>\n\n💵 Send amount (min ₹10):", parse_mode="HTML")
            elif d["cfg"].get("upi"):
                c.user_data["deposit"] = {"stage": "amount", "via": "manual"}
                await q.edit_message_text("💳 <b>Add Funds</b>\n\n💵 Send amount (min ₹10):", parse_mode="HTML")
            else:
                await q.edit_message_text("⚠️ Deposits not set up yet. Contact admin.")
                return

        elif data == "dep_paid":
            dep = c.user_data.get("deposit", {})
            if not dep.get("amount"):
                return
            dep["stage"] = "utr"
            await q.edit_message_text("✅ Payment done?\n\n📝 Now send your <b>UTR / Transaction ID</b> (12 digits):", parse_mode="HTML")

        elif data == "dep_cancel":
            c.user_data.pop("deposit", None)
            await q.edit_message_text("❌ Deposit cancelled.", reply_markup=main_menu(is_owner))

        elif data.startswith("gwcheck:"):
            did = data[8:]
            v = d["deposits"].get(did)
            if not v or v.get("uid") != str(uid):
                await q.edit_message_text("❌ Deposit not found.")
                return
            if v.get("status") != "pending_gw":
                await q.edit_message_text(f"Deposit already {v.get('status')}.", reply_markup=main_menu(is_owner))
                return
            await q.answer("Checking payment...")
            code, j = gb(d["cfg"], "GET", "/api/order_status",
                         {"api_key": d["cfg"].get("gateway_key"), "order_id": v.get("gw_order")})
            st = (j.get("status") or "").lower() if isinstance(j, dict) else ""
            if st == "paid":
                v["status"] = "approved"
                _add_bal(d, uid, v["amount"])
                _save(d)
                await q.edit_message_text(
                    f"✅ <b>Payment verified!</b> 🌉\n\n💰 ₹{v['amount']:.2f} added to your balance.\n"
                    f"New balance: ₹{_bal(d, uid):.2f}",
                    reply_markup=main_menu(is_owner), parse_mode="HTML")
            elif st == "expired":
                v["status"] = "expired"
                _save(d)
                await q.edit_message_text("⌛ This QR expired (15 min). Start a new deposit from 💳 Add Funds.",
                                          reply_markup=main_menu(is_owner))
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Check Again", callback_data=f"gwcheck:{did}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="dep_cancel")]])
                await q.edit_message_text(
                    "⏳ Payment not detected yet.\n\nPay the exact QR amount in your UPI app, then tap 🔄 Check Again.",
                    reply_markup=kb)

        # ----- ADMIN -----
        elif data == "admin":
            if not is_owner:
                await q.edit_message_text("❌ Admin only!")
                return
            await q.edit_message_text("⚙️ <b>Admin Panel</b>", reply_markup=admin_menu(d), parse_mode="HTML")

        elif data in ("adm_url", "adm_key", "adm_upi"):
            if not is_owner:
                return
            labels = {"adm_url": "SMM API URL (e.g. https://panel.com/api/v2)",
                      "adm_key": "SMM API Key", "adm_upi": "Your UPI ID for deposits (manual fallback)"}
            c.user_data["admin_set"] = data
            await q.edit_message_text(f"✍️ Send <b>{labels[data]}</b>:", parse_mode="HTML")

        elif data == "adm_gw":
            if not is_owner:
                return
            c.user_data["admin_set"] = "adm_gw"
            await q.edit_message_text(
                "🌉 <b>FamBridge Payment Gateway</b>\n\n"
                "✍️ Send your <b>Gateway API Key</b>\n"
                "(FamBridge bot → 🔑 My API Key)\n\n"
                "Once connected, all deposits auto-verify — no manual approval! 🚀\n\n"
                "Send <code>off</code> to disable.",
                parse_mode="HTML")

        elif data == "adm_test":
            if not is_owner:
                return
            j, err = smm(d["cfg"], "balance")
            if err:
                await q.edit_message_text(f"❌ API test failed: {err}", reply_markup=admin_menu(d))
            else:
                svcs, _ = get_services(d)
                await q.edit_message_text(f"✅ <b>API working!</b>\n🏦 Balance: {j.get('balance')} {j.get('currency','')}\n📦 Services: {len(svcs)}",
                                          reply_markup=admin_menu(d), parse_mode="HTML")

        elif data == "adm_deps":
            if not is_owner:
                return
            pend = [(k, v) for k, v in d["deposits"].items() if v["status"] == "pending"]
            if not pend:
                await q.edit_message_text("💳 No pending deposits.", reply_markup=admin_menu(d))
                return
            kb = []
            for k, v in pend:
                kb.append([InlineKeyboardButton(f"₹{v['amount']} — {v.get('name','?')} ({v.get('utr','?')})", callback_data=f"dep:{k}")])
            kb.append([InlineKeyboardButton("« Admin", callback_data="admin")])
            await q.edit_message_text("💳 <b>Pending deposits:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

        elif data.startswith("dep:"):
            if not is_owner:
                return
            did = data[4:]
            v = d["deposits"].get(did)
            if not v or v["status"] != "pending":
                await q.edit_message_text("Already handled.")
                return
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"depok:{did}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"depno:{did}")],
                [InlineKeyboardButton("« Deposits", callback_data="adm_deps")]])
            await q.edit_message_text(
                f"💳 <b>Deposit {did}</b>\n👤 {v.get('name')} (<code>{v.get('uid')}</code>)\n"
                f"💵 ₹{v['amount']}\n🔢 UTR: <code>{v.get('utr')}</code>",
                reply_markup=kb, parse_mode="HTML")

        elif data.startswith("depok:"):
            if not is_owner:
                return
            did = data[6:]
            v = d["deposits"].get(did)
            if v and v["status"] == "pending":
                v["status"] = "approved"
                _add_bal(d, v["uid"], v["amount"])
                _save(d)
                try:
                    await c.bot.send_message(v["uid"], f"✅ <b>Deposit approved!</b>\n💰 ₹{v['amount']:.2f} added.\nNew balance: ₹{_bal(d, v['uid']):.2f}", parse_mode="HTML")
                except Exception:
                    pass
            await q.edit_message_text(f"✅ Approved ₹{v['amount']}.", reply_markup=admin_menu(d))

        elif data.startswith("depno:"):
            if not is_owner:
                return
            did = data[6:]
            v = d["deposits"].get(did)
            if v and v["status"] == "pending":
                v["status"] = "rejected"
                _save(d)
                try:
                    await c.bot.send_message(v["uid"], "❌ Your deposit was rejected. Contact admin.")
                except Exception:
                    pass
            await q.edit_message_text("❌ Rejected.", reply_markup=admin_menu(d))

        elif data == "adm_addbal":
            if not is_owner:
                return
            c.user_data["admin_set"] = "adm_addbal"
            await q.edit_message_text("✍️ Send: <code>user_id amount</code>\nExample: <code>123456 100</code>", parse_mode="HTML")

        elif data == "adm_stats":
            if not is_owner:
                return
            users = len(d["users"])
            tot_dep = sum(v["amount"] for v in d["deposits"].values() if v["status"] == "approved")
            tot_ord = sum(v["charge"] for v in d["orders"].values())
            await q.edit_message_text(
                f"📊 <b>Stats</b>\n👥 Users: {users}\n💳 Deposits approved: ₹{tot_dep:.2f}\n🛒 Orders value: ₹{tot_ord:.2f}\n📦 Orders: {len(d['orders'])}",
                reply_markup=admin_menu(d), parse_mode="HTML")

    # ---------- text router (staged inputs) ----------
    async def text(u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        txt = u.message.text.strip()
        d = _db()
        is_owner = str(uid) == str(OWNER)

        # admin setup inputs
        aset = c.user_data.get("admin_set")
        if aset and is_owner:
            if aset == "adm_url":
                d["cfg"]["api_url"] = txt
                SVC_CACHE.update({"at": 0, "data": []})
            elif aset == "adm_key":
                d["cfg"]["api_key"] = txt
                SVC_CACHE.update({"at": 0, "data": []})
            elif aset == "adm_upi":
                d["cfg"]["upi"] = txt
            elif aset == "adm_gw":
                if txt.lower() == "off":
                    d["cfg"].pop("gateway_key", None)
                    _save(d)
                    c.user_data.pop("admin_set", None)
                    await u.message.reply_text("🌉 Gateway disabled. Manual UPI deposits will be used.", reply_markup=admin_menu(d))
                    return
                # validate key: fake order -> 404 means key OK, 401 means bad key
                code, j = gb(d["cfg"], "GET", "/api/order_status",
                             {"api_key": txt, "order_id": "ord_keycheck000"})
                if code == 401:
                    await u.message.reply_text("❌ Invalid API key! Copy it again from FamBridge bot → 🔑 My API Key.")
                    return
                if code == 0:
                    await u.message.reply_text(f"❌ Cannot reach gateway: {j.get('error')}. Try again later.")
                    return
                d["cfg"]["gateway_key"] = txt
                _save(d)
                c.user_data.pop("admin_set", None)
                await u.message.reply_text("🌉 <b>Gateway connected!</b> ✅\n\nAll deposits will now <b>auto-verify</b> — no manual approval needed! 🚀",
                                           reply_markup=admin_menu(d), parse_mode="HTML")
                return
            elif aset == "adm_addbal":
                try:
                    parts = txt.split()
                    _add_bal(d, parts[0], float(parts[1]))
                    await u.message.reply_text(f"✅ Added ₹{float(parts[1]):.2f} to {parts[0]}")
                except Exception:
                    await u.message.reply_text("❌ Format: user_id amount")
                    return
                _save(d)
                c.user_data.pop("admin_set", None)
                return
            else:
                c.user_data.pop("admin_set", None)
                return
            _save(d)
            c.user_data.pop("admin_set", None)
            await u.message.reply_text("✅ Saved!", reply_markup=admin_menu(d))
            return

        # order flow: link then quantity
        o = c.user_data.get("order")
        if o:
            if o["stage"] == "link":
                if not txt.startswith("http"):
                    await u.message.reply_text("❌ Send a valid link (starting with http)")
                    return
                o["link"] = txt
                o["stage"] = "qty"
                s = o["service"]
                await u.message.reply_text(f"🔗 Link saved!\n\n🔢 Send <b>quantity</b> (min {s.get('min')}, max {s.get('max')}):", parse_mode="HTML")
                return
            if o["stage"] == "qty":
                s = o["service"]
                try:
                    qty = int(txt)
                    assert int(s.get("min", 0)) <= qty <= int(s.get("max", 10**9))
                except Exception:
                    await u.message.reply_text(f"❌ Quantity must be between {s.get('min')} and {s.get('max')}")
                    return
                o["qty"] = qty
                charge = round(float(s.get("rate", 0)) * qty / 1000, 2)
                o["stage"] = "confirm"
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirm Order", callback_data="order_confirm")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="order_cancel")]])
                await u.message.reply_text(
                    f"🧾 <b>Confirm order:</b>\n\n📦 {s.get('name')}\n🔗 {o['link'][:50]}\n"
                    f"🔢 Qty: {qty}\n💵 Charge: ₹{charge:.2f}\n💰 Your balance: ₹{_bal(d, uid):.2f}",
                    reply_markup=kb, parse_mode="HTML")
                return

        # deposit flow
        dep = c.user_data.get("deposit")
        if dep:
            if dep["stage"] == "amount":
                try:
                    amt = float(txt)
                    assert amt >= 10
                except Exception:
                    await u.message.reply_text("❌ Amount must be ₹10 or more.")
                    return
                dep["amount"] = round(amt, 2)
                # ---- FamBridge gateway auto-payment ----
                if dep.get("via") == "gateway":
                    code, j = gb(d["cfg"], "POST", "/api/create_order",
                                 {"api_key": d["cfg"].get("gateway_key"),
                                  "amount": dep["amount"],
                                  "note": f"SMM deposit {u.effective_user.first_name}"})
                    if code != 200 or not isinstance(j, dict) or not j.get("order_id"):
                        c.user_data.pop("deposit", None)
                        await u.message.reply_text(
                            f"❌ Gateway error ({code}): {j.get('error', 'unknown') if isinstance(j, dict) else 'no response'}\n"
                            "Try again or contact admin.", reply_markup=main_menu(is_owner))
                        return
                    did = f"D{int(time.time())}"
                    d["deposits"][did] = {"uid": str(uid), "name": u.effective_user.first_name,
                                          "amount": dep["amount"], "gw_order": j["order_id"],
                                          "status": "pending_gw", "at": time.time()}
                    _save(d)
                    c.user_data.pop("deposit", None)
                    import base64 as _b64
                    qr_bytes = _b64.b64decode(j["qr_base64"])
                    pay_amt = j.get("amount_paise", int(dep["amount"] * 100)) / 100
                    kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Check Payment Status", callback_data=f"gwcheck:{did}")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="dep_cancel")]])
                    await u.message.reply_photo(
                        qr_bytes,
                        caption=f"💳 <b>Pay ₹{pay_amt:.2f}</b> via any UPI app 🌉\n\n"
                                f"⏳ QR valid for 15 min.\nPay, then tap 🔄 Check Payment Status",
                        reply_markup=kb, parse_mode="HTML")
                    return
                # ---- manual UPI fallback ----
                dep["stage"] = "pay"
                upi = d["cfg"]["upi"]
                params = urllib.parse.urlencode({"pa": upi, "pn": "SMM Panel", "am": f"{amt:.2f}", "cu": "INR"})
                link = f"upi://pay?{params}"
                qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link)}"
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ I've Paid", callback_data="dep_paid")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="dep_cancel")]])
                await u.message.reply_photo(qr, caption=f"💳 <b>Pay ₹{amt:.2f}</b>\nUPI: <code>{upi}</code>\n\nPay then tap ✅ I've Paid",
                                            reply_markup=kb, parse_mode="HTML")
                return
            if dep["stage"] == "utr":
                if not re.search(r"\d{6,}", txt):
                    await u.message.reply_text("❌ Send a valid UTR / transaction ID.")
                    return
                did = f"D{int(time.time())}"
                d["deposits"][did] = {"uid": str(uid), "name": u.effective_user.first_name,
                                      "amount": dep["amount"], "utr": txt, "status": "pending", "at": time.time()}
                _save(d)
                c.user_data.pop("deposit", None)
                if OWNER:
                    try:
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Review", callback_data=f"dep:{did}")]])
                        await c.bot.send_message(OWNER, f"💳 <b>New deposit!</b>\n👤 {u.effective_user.first_name}\n💵 ₹{dep['amount']:.2f}\n🔢 <code>{txt}</code>",
                                                 reply_markup=kb, parse_mode="HTML")
                    except Exception:
                        pass
                await u.message.reply_text("⏳ <b>Deposit submitted!</b>\nAdmin will approve shortly.", reply_markup=main_menu(is_owner), parse_mode="HTML")
                return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", lambda u, c: btn(u, c)))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    print("SMM Panel Pro template loaded", flush=True)
    app.run_polling()
