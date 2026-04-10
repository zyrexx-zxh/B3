#Made By @Claxen

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
import json
import html

# ⚙️ CONFIG (SYSTEM PARAMS)
BOT_TOKEN = '8217485020:AAHUAQnFeL0hmkXNJ2ZjNddWt3oe-UfLVbc'
ADMIN_GROUP_ID = -1003943618778  
BOT_NAME = "B3 COMPLAINT BOT" 

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂️ DATABASE FILES (Persistence)
USERS_FILE = 'users.txt'
TICKETS_FILE = 'tickets.json'

tickets_db = {} 
banned_users = set()
user_sessions = {} 
registered_users = set()

def load_data():
    global tickets_db, registered_users
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            tickets_db = json.load(f)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if line.strip(): registered_users.add(int(line.strip()))

def save_tickets():
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets_db, f)

load_data()

BAD_WORDS = [
    'bc', 'mc', 'tmkc', 'rndi', 'rndy', 'randi', 'randy', 
    'teri maa ki chut', 'teri bhen ki chut', 'teri bhen chod dunga', 
    'chod', 'land', 'lund', 'bhosda', 'aulaad'
]

def is_abusive(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower: return True
    return False

@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def handle_banned(message):
    bot.reply_to(message, "🛑 <b>ACCESS DENIED</b> 🛑\nYou are banned from using this portal due to rule violations.", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    
    if uid not in registered_users:
        registered_users.add(uid)
        with open(USERS_FILE, 'a') as f:
            f.write(f"{uid}\n")
    
    if uid not in user_sessions:
        user_sessions[uid] = {}
    
    user_sessions[uid]['name'] = message.from_user.first_name
    
    welcome_msg = (
        f"🏫 ✨ <b>Welcome to the {BOT_NAME}</b> ✨ 🏫\n\n"
        "🌐 Choose Language / अपनी भाषा चुनें 🗣️:\n\n"
        "💡 <i>Note: Use /help command if you are stuck.</i>"
    )
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="l_en"), 
               InlineKeyboardButton("🇮🇳 हिंदी", callback_data="l_hi"))
    bot.send_message(uid, welcome_msg, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    uid = message.chat.id
    
    if uid == ADMIN_GROUP_ID:
        admin_help = (
            "👑 <b>ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━━\n"
            "📊 /stats - Live Data Analytics\n"
            "📢 /broadcast &lt;msg&gt; - Mass Push Alert\n"
            "📁 /report - Generate HTML Dashboard\n"
            "🔓 /unban &lt;UserID&gt; - Unblock a User"
        )
        return bot.reply_to(message, admin_help, parse_mode="HTML")

    lang = user_sessions.get(uid, {}).get('lang', 'en')
    if lang == 'en':
        help_text = (
            "🛠️ <b>HELP MENU</b>\n━━━━━━━━━━━━━━\n"
            "🚀 /start - Start new complaint\n"
            "🔎 /status &lt;ID&gt; - Check progress\n"
            "🗑️ /delete &lt;ID&gt; - Delete your ticket"
        )
    else:
        help_text = (
            "🛠️ <b>सहायता मेनू</b>\n━━━━━━━━━━━━━━\n"
            "🚀 /start - नई शिकायत दर्ज करें\n"
            "🔎 /status &lt;ID&gt; - प्रोग्रेस देखें\n"
            "🗑️ /delete &lt;ID&gt; - अपनी टिकट मिटाएं"
        )
    bot.reply_to(message, help_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith('l_'))
def set_lang(call):
    uid = call.message.chat.id
    lang = call.data.split('_')[1]
    user_sessions[uid]['lang'] = lang
    
    markup = InlineKeyboardMarkup(row_width=1)
    # Changed to clean, universal single-character emojis
    cats = ["🎒 Student Dispute", "💼 Staff Issue", "🏢 Infrastructure", "📌 Other"] if lang == 'en' else ["🎒 छात्र विवाद", "💼 स्टाफ समस्या", "🏢 प्रॉपर्टी", "📌 अन्य"]
    for i, cat in enumerate(["Student", "Staff", "Infra", "Other"]):
        markup.add(InlineKeyboardButton(cats[i], callback_data=f"c_{cat}"))
    bot.edit_message_text("📂 Select Category:" if lang == 'en' else "📂 कैटेगरी चुनें:", uid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def ask_text(call):
    uid = call.message.chat.id
    user_sessions[uid]['cat'] = call.data.split('_')[1]
    msg = "✍️ Type your complete complaint:" if user_sessions[uid]['lang'] == 'en' else "✍️ अपनी शिकायत विस्तार से लिखें:"
    bot.edit_message_text(msg, uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    text = message.text
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    
    if is_abusive(text):
        warn_msg = "⚠️ <b>ACTION BLOCKED!</b> ⚠️\nInappropriate language." if lang == 'en' else "⚠️ <b>ब्लॉक कर दिया गया!</b> ⚠️\nआपत्तिजनक भाषा है।"
        bot.reply_to(message, warn_msg, parse_mode="HTML")
        safe_attempt = html.escape(text)
        bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>ABUSE ALERT</b>\nID: <code>{uid}</code>\nAttempt: <i>{safe_attempt}</i>", parse_mode="HTML")
        return

    user_sessions[uid]['text'] = html.escape(text)
    
    markup = InlineKeyboardMarkup(row_width=1)
    if lang == 'en':
        markup.add(InlineKeyboardButton("🕵️ Anonymous", callback_data="s_anon"), InlineKeyboardButton("👤 With Name", callback_data="s_name"))
        bot.send_message(uid, "🛡️ Privacy Mode:", reply_markup=markup)
    else:
        markup.add(InlineKeyboardButton("🕵️ गुप्त", callback_data="s_anon"), InlineKeyboardButton("👤 नाम के साथ", callback_data="s_name"))
        bot.send_message(uid, "🛡️ प्राइवेसी मोड:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['send_anon', 'send_name', 's_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    if uid not in user_sessions or 'text' not in user_sessions[uid]: return

    data = user_sessions[uid]
    tid = f"T{random.randint(1000, 9999)}"
    identity = "Anonymous 🕵️" if call.data == 's_anon' else f"{html.escape(data['name'])} 👤"
    
    admin_markup = InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{uid}")
    )
    
    try:
        admin_msg = bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>NEW TICKET: {tid}</b>\nFrom: {identity}\nIssue: <i>{data['text']}</i>\nStatus: <b>🆕 Unread</b>", reply_markup=admin_markup, parse_mode="HTML")
        
        tickets_db[tid] = {'uid': uid, 'text': data['text'], 'status': '🆕 Unread', 'cat': data['cat'], 'lang': data['lang'], 'admin_msg_id': admin_msg.message_id}
        save_tickets()
        
        if data['lang'] == 'en':
            conf = f"✅ <b>SUBMITTED!</b> ID: <code>{tid}</code>\n📝 <i>Note: Use /status {tid} for progress.</i>" 
        else:
            conf = f"✅ <b>भेज दिया!</b> ID: <code>{tid}</code>\n📝 <i>नोट: प्रोग्रेस देखें /status {tid} से।</i>"
        bot.edit_message_text(conf, uid, call.message.message_id, parse_mode="HTML")
        del user_sessions[uid]
    except Exception as e:
        bot.answer_callback_query(call.id, "⚠️ Error sending to admin group.")

@bot.message_handler(commands=['status'])
def check_status(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Usage: <code>/status T1234</code>" if lang == 'en' else "<code>/status T1234</code>", parse_mode="HTML")
    
    tid = args[1].upper()
    if tid in tickets_db:
        t = tickets_db[tid]
        bot.reply_to(message, f"🎫 <b>TICKET: {tid}</b>\nStatus: <b>{t['status']}</b>\nCat: {t['cat']}", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Not Found.")

@bot.message_handler(commands=['delete'])
def delete_ticket(message):
    uid = message.chat.id
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Usage: <code>/delete T1234</code>", parse_mode="HTML")
    
    tid = args[1].upper()
    if tid in tickets_db and tickets_db[tid]['uid'] == uid:
        mid = tickets_db[tid].get('admin_msg_id')
        del tickets_db[tid]
        save_tickets()
        bot.reply_to(message, "🗑️ <b>Deleted.</b>", parse_mode="HTML")
        if mid:
            try: bot.delete_message(ADMIN_GROUP_ID, mid)
            except Exception: pass
    else:
        bot.reply_to(message, "❌ Denied.")

@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    total = len(tickets_db)
    bot.reply_to(message, f"📊 <b>LIVE ANALYTICS</b>\n━━━━━━━━━━━━━━\n📝 Total Tickets: <b>{total}</b>\n👥 Permanent Users: <b>{len(registered_users)}</b>", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast_message(message):
    args = message.text.split(' ', 1)
    if len(args) < 2: return
    b_msg = html.escape(args[1])
    for uid in list(registered_users):
        try: bot.send_message(uid, f"📢 <b>ADMIN ANNOUNCEMENT</b>\n━━━━━━━━━━━━━━\n{b_msg}", parse_mode="HTML")
        except Exception: pass
    bot.reply_to(message, "✅ <b>Broadcast Sent.</b>", parse_mode="HTML")

@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def export_report(message):
    filename = "B3_Complaint_Dashboard.html"
    colors = {'✅ Solved': '#2ea043', '❌ Rejected': '#f85149', '⚙️ Working': '#d29922', '⏳ Pending': '#8b949e', '🆕 Unread': '#58a6ff'}
    
    html_report = f"""<!DOCTYPE html><html><head><style>
        body {{ background:#0d1117; color:#c9d1d9; font-family: 'Segoe UI', sans-serif; padding:20px; }}
        h1 {{ text-align:center; color:#58a6ff; margin: 0; padding-bottom:10px; border-bottom: 2px solid #58a6ff;}}
        .header {{ text-align: center; color: #8b949e; font-size: 13px; margin-top: 5px; margin-bottom: 20px; }}
        table {{ width:100%; border-collapse:collapse; background:#161b22; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 8px; overflow: hidden; }}
        th, td {{ padding:12px; border:1px solid #30363d; text-align:left; }}
        th {{ background:#21262d; color:#8b949e; text-transform:uppercase; font-size:12px; }}
        .badge {{ padding:6px 12px; border-radius:4px; font-size:12px; font-weight:bold; color:white; letter-spacing: 0.5px; }}
        tr:hover {{ background-color: #1f2428; }}
        .footer {{ margin-top:30px; text-align:center; color:#8b949e; font-size:12px; font-weight:bold;}}
    </style></head><body><h1>🛡️ {BOT_NAME} DASHBOARD 🛡️</h1><div class="header">Generated by @Claxen System</div><table><thead><tr><th>ID</th><th>Category</th><th>Current Status</th><th>User Complaint</th></tr></thead><tbody>"""
    
    for tid, d in tickets_db.items():
        bg = colors.get(d['status'], '#58a6ff')
        html_report += f"""<tr><td style="color:#f85149; font-family:monospace;">{tid}</td><td>{d['cat']}</td><td><span class='badge' style='background:{bg};'>{d['status']}</span></td><td style="color: #c9d1d9">{d['text']}</td></tr>"""
    
    html_report += """</tbody></table><div class="footer">Confidential Report • Made for B3 • Powered by Claxen Systems</div></body></html>"""
    
    with open(filename, 'w', encoding='utf-8') as f: f.write(html_report)
    with open(filename, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f, caption="📊 Premium Metallic Dashboard")
    os.remove(filename)

@bot.callback_query_handler(func=lambda c: c.data.startswith('admin_ban_') or c.data.startswith('st_'))
def handle_admin_actions(call):
    if call.data.startswith('admin_ban_'):
        uid = int(call.data.split('_')[2])
        banned_users.add(uid)
        bot.answer_callback_query(call.id, "User Banned! 🚫")
        lang = user_sessions.get(uid, {}).get('lang', 'en')
        msg = "🚫 <b>ACCOUNT BANNED</b> for rules violation." if lang == 'en' else "🚫 <b>अकाउंट ब्लॉक</b> नियमों के उल्लंघन के कारण आपको ब्लॉक कर दिया गया है।"
        try: bot.send_message(uid, msg, parse_mode="HTML")
        except Exception: pass
        return

    _, action, sid, tid = call.data.split('_')
    sid = int(sid)
    
    status_map = {
        'rej': {'label': '❌ Rejected', 'en': f"❌ <b>TICKET REJECTED ({tid})</b>\nUnfortunately, your complaint has been rejected by administration. Possible reasons include insufficient info or no violation of school policies.", 'hi': f"❌ <b>रिपोर्ट खारिज ({tid})</b>\nक्षमा करें, स्कूल प्रशासन ने आपकी शिकायत को खारिज कर दिया है। इसका कारण अधूरी जानकारी या नियमों का उल्लंघन नहीं होना हो सकता है।"},
        'pen': {'label': '⏳ Pending', 'en': f"⏳ <b>TICKET PENDING ({tid})</b>\nYour report has been placed in the pending queue. We are reviewing complaints sequentially.", 'hi': f"⏳ <b>प्रोग्रेस अपडेट ({tid})</b>\nआपकी रिपोर्ट अभी पेंडिंग में है। हमारी टीम जल्द ही इसकी समीक्षा करेगी।"},
        'wrk': {'label': '⚙️ Working', 'en': f"⚙️ <b>INVESTIGATION STARTED ({tid})</b>\nExcellent news! School administration has started an investigation based on your report. We are actively working to fix the issue.", 'hi': f"⚙️ <b>कार्यवाही शुरू ({tid})</b>\nअच्छी खबर! स्कूल प्रशासन ने आपकी शिकायत पर जांच शुरू कर दी है। हम समस्या को जल्द ही सुलझा लेंगे।"},
        'sol': {'label': '✅ Solved', 'en': f"✅ <b>ISSUE RESOLVED ({tid})</b>\nThe school administration has successfully resolved your complaint. Thank you for helping us make B3 safer!", 'hi': f"✅ <b>समस्या का समाधान! ({tid})</b>\nस्कूल प्रशासन ने आपकी शिकायत का सफलतापूर्वक समाधान कर लिया है। B3 को सुरक्षित बनाने में मदद करने के लिए धन्यवाद!"}
    }
    
    current = status_map.get(action, {})
    if not current: return
    
    if tid in tickets_db:
        tickets_db[tid]['status'] = current['label']
        save_tickets()
        
        old_text = call.message.text
        new_text = html.escape(old_text.split('Status:')[0]) + f"Status: <b>{current['label']}</b>"
        bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        
        lang = tickets_db[tid].get('lang', 'en')
        notif_text = current[lang]
        try: bot.send_message(sid, notif_text, parse_mode="HTML")
        except Exception: pass

bot.polling(none_stop=True)
