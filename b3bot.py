#Made By @Claxen

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
import json
import html
import re

# ⚙️ CONFIG
BOT_TOKEN = '8217485020:AAHUAQnFeL0hmkXNJ2ZjNddWt3oe-UfLVbc'
ADMIN_GROUP_ID = -1003943618778  
BOT_NAME = "B3 COMPLAINT BOT" 

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂️ DATABASE FILES
USERS_FILE = 'users.txt'
TICKETS_FILE = 'tickets.json'

tickets_db = {} 
banned_users = set()
user_sessions = {} 
registered_users = set()

# function to strip emojis from the dashboard text
def strip_emojis(text):
    return re.sub(r'[^\x00-\x7f]', r'', text).strip()

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
    bot.reply_to(message, "🛑 <b>ACCESS DENIED</b>\nYou are banned for rule violations.", parse_mode="HTML")

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
    
    # admin help in GC
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
    help_text = "🛠️ <b>HELP MENU</b>\n🚀 /start\n🔎 /status\n🗑️ /delete" if lang == 'en' else "🛠️ <b>सहायता</b>\n🚀 /start\n🔎 /status\n🗑️ /delete"
    bot.reply_to(message, help_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith('l_'))
def set_lang(call):
    uid = call.message.chat.id
    lang = call.data.split('_')[1]
    user_sessions[uid]['lang'] = lang
    
    markup = InlineKeyboardMarkup(row_width=1)
    cats = ["🎒 Student Dispute", "💼 Staff Issue", "🏢 Infrastructure", "📌 Other"] if lang == 'en' else ["🎒 छात्र विवाद", "💼 स्टाफ समस्या", "🏢 प्रॉपर्टी", "📌 अन्य"]
    for i, cat in enumerate(["Student", "Staff", "Infra", "Other"]):
        markup.add(InlineKeyboardButton(cats[i], callback_data=f"c_{cat}"))
    bot.edit_message_text("📂 Select Category:" if lang == 'en' else "📂 कैटेगरी चुनें:", uid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def ask_text(call):
    uid = call.message.chat.id
    user_sessions[uid]['cat'] = call.data.split('_')[1]
    msg = "✍️ Type your complaint:" if user_sessions[uid]['lang'] == 'en' else "✍️ अपनी शिकायत लिखें:"
    bot.edit_message_text(msg, uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    if is_abusive(message.text):
        bot.reply_to(message, "⚠️ <b>ACTION BLOCKED!</b>", parse_mode="HTML")
        bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>ABUSE ALERT</b>\nID: <code>{uid}</code>", parse_mode="HTML")
        return
    
    user_sessions[uid]['text'] = html.escape(message.text)
    lang = user_sessions[uid]['lang']
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🕵️ Anonymous", callback_data="s_anon"), InlineKeyboardButton("👤 With Name", callback_data="s_name"))
    bot.send_message(uid, "🛡️ Privacy Mode:" if lang == 'en' else "🛡️ प्राइवेसी मोड:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['s_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    data = user_sessions.get(uid)
    tid = f"T{random.randint(1000, 9999)}"
    identity = "Anonymous" if call.data == 's_anon' else f"{html.escape(data['name'])}"
    
    admin_markup = InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{uid}")
    )
    
    admin_msg = bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>NEW TICKET: {tid}</b>\nFrom: {identity}\nIssue: <i>{data['text']}</i>\nStatus: <b>🆕 Unread</b>", reply_markup=admin_markup, parse_mode="HTML")
    tickets_db[tid] = {'uid': uid, 'text': data['text'], 'status': '🆕 Unread', 'cat': data['cat'], 'lang': data['lang'], 'admin_msg_id': admin_msg.message_id}
    save_tickets()
    bot.edit_message_text(f"✅ <b>SUBMITTED!</b> ID: <code>{tid}</code>", uid, call.message.message_id, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def check_status(message):
    args = message.text.split()
    if len(args) < 2: return
    tid = args[1].upper()
    if tid in tickets_db:
        bot.reply_to(message, f"🎫 <b>TICKET: {tid}</b>\nStatus: <b>{tickets_db[tid]['status']}</b>", parse_mode="HTML")

@bot.message_handler(commands=['delete'])
def delete_ticket(message):
    args = message.text.split()
    if len(args) < 2: return
    tid = args[1].upper()
    if tid in tickets_db and tickets_db[tid]['uid'] == message.chat.id:
        mid = tickets_db[tid].get('admin_msg_id')
        del tickets_db[tid]
        save_tickets()
        bot.reply_to(message, "🗑️ <b>Deleted.</b>", parse_mode="HTML")
        if mid:
            try: bot.delete_message(ADMIN_GROUP_ID, mid)
            except: pass

@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    total = len(tickets_db)
    bot.reply_to(message, f"📊 <b>STATS</b>\nTotal: {total}\nUsers: {len(registered_users)}", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast_message(message):
    args = message.text.split(' ', 1)
    if len(args) < 2: return
    for uid in list(registered_users):
        try: bot.send_message(uid, f"📢 <b>ANNOUNCEMENT</b>\n\n{html.escape(args[1])}", parse_mode="HTML")
        except: pass
    bot.reply_to(message, "✅ Broadcast Sent.")

@bot.message_handler(commands=['unban'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def unban_user(message):
    args = message.text.split()
    if len(args) < 2: return
    try:
        uid = int(args[1])
        if uid in banned_users:
            banned_users.remove(uid)
            bot.reply_to(message, f"✅ User {uid} Unbanned.")
    except: pass

@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def export_report(message):
    filename = "B3_Dashboard.html"
    colors = {'Solved': '#2ea043', 'Rejected': '#f85149', 'Working': '#d29922', 'Pending': '#8b949e', 'Unread': '#58a6ff'}
    
    html_report = f"""<!DOCTYPE html><html><head><style>
        body {{ background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px; }}
        h1 {{ text-align:center; color:#58a6ff; border-bottom: 2px solid #58a6ff; padding-bottom:10px; }}
        table {{ width:100%; border-collapse:collapse; background:#161b22; margin-top:20px; }}
        th, td {{ padding:12px; border:1px solid #30363d; text-align:left; }}
        th {{ background:#21262d; color:#8b949e; text-transform:uppercase; font-size:12px; }}
        .badge {{ padding:5px 10px; border-radius:4px; font-size:11px; font-weight:bold; color:white; }}
        .footer {{ margin-top:30px; text-align:center; color:#8b949e; font-size:12px; }}
    </style></head><body><h1>🛡️ {BOT_NAME} DASHBOARD </h1><table><thead><tr><th>ID</th><th>Category</th><th>Status</th><th>Complaint</th></tr></thead><tbody>"""
    
    for tid, d in tickets_db.items():
        c_status = strip_emojis(d['status'])
        c_cat = strip_emojis(d['cat'])
        bg = colors.get(c_status, '#58a6ff')
        html_report += f"<tr><td>{tid}</td><td>{c_cat}</td><td><span class='badge' style='background:{bg};'>{c_status.upper()}</span></td><td>{d['text']}</td></tr>"
    
    html_report += "</tbody></table></body></html>"
    with open(filename, 'w', encoding='utf-8') as f: f.write(html_report)
    with open(filename, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f)
    os.remove(filename)

@bot.callback_query_handler(func=lambda c: c.data.startswith('st_') or c.data.startswith('admin_ban_'))
def handle_admin(call):
    if 'ban' in call.data:
        uid = int(call.data.split('_')[2])
        banned_users.add(uid)
        bot.answer_callback_query(call.id, "Banned!")
        return
    
    _, action, sid, tid = call.data.split('_')
    status_map = {
        'rej': {'label': '❌ Rejected', 'en': f"❌ <b>TICKET REJECTED ({tid})</b>\nYour complaint has been rejected by administration.", 'hi': f"❌ <b>रिपोर्ट खारिज ({tid})</b>\nआपकी शिकायत को खारिज कर दिया गया है।"},
        'pen': {'label': '⏳ Pending', 'en': f"⏳ <b>TICKET PENDING ({tid})</b>\nYour report is currently in the pending queue.", 'hi': f"⏳ <b>पेंडिंग अपडेट ({tid})</b>\nआपकी रिपोर्ट अभी पेंडing में है।"},
        'wrk': {'label': '⚙️ Working', 'en': f"⚙️ <b>INVESTIGATION STARTED ({tid})</b>\nExcellent news! School administration has started an investigation.", 'hi': f"⚙️ <b>जांच शुरू ({tid})</b>\nस्कूल प्रशासन ने आपकी शिकायत पर जांच शुरू कर दी है।"},
        'sol': {'label': '✅ Solved', 'en': f"✅ <b>ISSUE RESOLVED ({tid})</b>\nThe administration has successfully resolved your complaint.", 'hi': f"✅ <b>समस्या का समाधान! ({tid})</b>\nप्रशासन ने आपकी शिकायत सुलझा ली है।"}
    }
    
    current = status_map.get(action)
    if tid in tickets_db:
        tickets_db[tid]['status'] = current['label']
        save_tickets()
        bot.edit_message_text(call.message.text.split('Status:')[0] + f"Status: <b>{current['label']}</b>", call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        lang = tickets_db[tid].get('lang', 'en')
        try: bot.send_message(int(sid), current[lang], parse_mode="HTML")
        except: pass

bot.polling(none_stop=True)
        
