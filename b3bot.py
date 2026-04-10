# Made By @Claxen - Final Version for Render
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
import json
import html
import re
from flask import Flask
from threading import Thread

# ⚙️ CONFIG
BOT_TOKEN = '8217485020:AAHUAQnFeL0hmkXNJ2ZjNddWt3oe-UfLVbc'
ADMIN_GROUP_ID = -1003943618778  
BOT_NAME = "B3 COMPLAINT BOT" 

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask('')

# Render Port Fix (Fake Web Server)
@server.route('/')
def home():
    return "Bot is Alive & Running! 🚀"

def run():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 🗂️ DATABASE
USERS_FILE = 'users.txt'
TICKETS_FILE = 'tickets.json'

tickets_db = {} 
banned_users = set()
user_sessions = {} 
registered_users = set()

# Clean Emojis for Report
def strip_emojis(text):
    return re.sub(r'[^\x00-\x7f]', r'', text).strip()

def load_data():
    global tickets_db, registered_users
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, 'r') as f: tickets_db = json.load(f)
        except: pass
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if line.strip(): registered_users.add(int(line.strip()))

def save_tickets():
    with open(TICKETS_FILE, 'w') as f: json.dump(tickets_db, f)

load_data()

BAD_WORDS = ['bc', 'mc', 'tmkc', 'rndi', 'randi', 'chod', 'lund', 'land', 'bhosda']

def is_abusive(text):
    t = text.lower()
    return any(word in t for word in BAD_WORDS)

@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def handle_banned(message):
    bot.reply_to(message, "🛑 <b>ACCESS DENIED</b>\nYou are banned.", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    if uid not in registered_users:
        registered_users.add(uid)
        with open(USERS_FILE, 'a') as f: f.write(f"{uid}\n")
    user_sessions[uid] = {'name': message.from_user.first_name}
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="l_en"), InlineKeyboardButton("🇮🇳 हिंदी", callback_data="l_hi"))
    bot.send_message(uid, f"🏫 <b>Welcome to {BOT_NAME}</b>\nChoose Language:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    uid = message.chat.id
    if uid == ADMIN_GROUP_ID:
        return bot.reply_to(message, "👑 <b>ADMIN</b>\n/stats - Data\n/broadcast <msg> - Alert\n/report - HTML\n/unban <ID> - Unblock", parse_mode="HTML")
    bot.reply_to(message, "🛠 /start | /status | /delete", parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith('l_'))
def set_lang(call):
    uid = call.message.chat.id
    user_sessions[uid]['lang'] = call.data.split('_')[1]
    markup = InlineKeyboardMarkup(row_width=1)
    cats = ["🎒 Student Dispute", "💼 Staff Issue", "🏢 Infrastructure", "📌 Other"]
    for cat in ["Student", "Staff", "Infra", "Other"]:
        markup.add(InlineKeyboardButton(cats[len(markup.keyboard)], callback_data=f"c_{cat}"))
    bot.edit_message_text("📂 Select Category:", uid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def ask_text(call):
    uid = call.message.chat.id
    user_sessions[uid]['cat'] = call.data.split('_')[1]
    bot.edit_message_text("✍️ Type your complaint:", uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    if is_abusive(message.text):
        bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>ABUSE:</b> {uid}\nContent: {message.text}", parse_mode="HTML")
        return bot.reply_to(message, "⚠️ Inappropriate language detected!")
    user_sessions[uid]['text'] = html.escape(message.text)
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🕵️ Anonymous", callback_data="s_anon"), InlineKeyboardButton("👤 With Name", callback_data="s_name"))
    bot.send_message(uid, "🛡 Privacy Mode:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['s_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    data = user_sessions.get(uid)
    tid = f"T{random.randint(1000, 9999)}"
    identity = "Anonymous" if call.data == 's_anon' else data['name']
    
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{uid}")
    )
    
    admin_msg = bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>TICKET: {tid}</b>\nFrom: {identity}\nIssue: {data['text']}\nStatus: 🆕 Unread", reply_markup=markup, parse_mode="HTML")
    tickets_db[tid] = {'uid': uid, 'text': data['text'], 'status': '🆕 Unread', 'cat': data['cat'], 'lang': data['lang'], 'admin_msg_id': admin_msg.message_id}
    save_tickets()
    bot.edit_message_text(f"✅ <b>SENT!</b> ID: <code>{tid}</code>", uid, call.message.message_id, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def check_status(message):
    args = message.text.split()
    if len(args) < 2: return
    tid = args[1].upper()
    if tid in tickets_db: bot.reply_to(message, f"🎫 <b>{tid} Status:</b> {tickets_db[tid]['status']}", parse_mode="HTML")

@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    bot.reply_to(message, f"📊 Total: {len(tickets_db)}\nUsers: {len(registered_users)}", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast(message):
    msg = message.text.split(' ', 1)
    if len(msg) < 2: return
    for u in list(registered_users):
        try: bot.send_message(u, f"📢 <b>ANNOUNCEMENT:</b>\n{msg[1]}", parse_mode="HTML")
        except: pass
    bot.reply_to(message, "✅ Sent.")

@bot.message_handler(commands=['unban'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def unban(message):
    try:
        uid = int(message.text.split()[1])
        if uid in banned_users: banned_users.remove(uid)
        bot.reply_to(message, f"✅ {uid} Unbanned.")
    except: pass

@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def report(message):
    fn = "B3_Report.html"
    colors = {'Solved': '#2ea043', 'Rejected': '#f85149', 'Working': '#d29922', 'Pending': '#8b949e', 'Unread': '#58a6ff'}
    html_c = "<html><head><style>body{background:#0d1117;color:#c9d1d9;font-family:sans-serif;}table{width:100%;border-collapse:collapse;}th,td{padding:10px;border:1px solid #30363d;}th{background:#21262d;}.badge{padding:4px;border-radius:4px;color:white;font-size:10px;}</style></head><body><h1 style='text-align:center;'>B3 DASHBOARD</h1><table><tr><th>ID</th><th>Cat</th><th>Status</th><th>Complaint</th></tr>"
    for tid, d in tickets_db.items():
        st = strip_emojis(d['status'])
        html_c += f"<tr><td>{tid}</td><td>{strip_emojis(d['cat'])}</td><td><span class='badge' style='background:{colors.get(st, '#58a6ff')};'>{st}</span></td><td>{d['text']}</td></tr>"
    html_c += "</table></body></html>"
    with open(fn, 'w', encoding='utf-8') as f: f.write(html_c)
    with open(fn, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f)
    os.remove(fn)

@bot.callback_query_handler(func=lambda c: c.data.startswith('st_') or c.data.startswith('admin_ban_'))
def handle_admin(call):
    if 'ban' in call.data:
        uid = int(call.data.split('_')[2]); banned_users.add(uid)
        return bot.answer_callback_query(call.id, "Banned!")
    _, act, sid, tid = call.data.split('_')
    s_map = {'rej': ('❌ Rejected', 'Rejected.'), 'pen': ('⏳ Pending', 'In queue.'), 'wrk': ('⚙️ Working', 'Investigation on!'), 'sol': ('✅ Solved', 'Resolved!')}
    label, note = s_map[act]
    if tid in tickets_db:
        tickets_db[tid]['status'] = label
        save_tickets()
        bot.edit_message_text(call.message.text.split('Status:')[0] + f"Status: <b>{label}</b>", call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        try: bot.send_message(int(sid), f"🔔 <b>Update {tid}:</b> {note}", parse_mode="HTML")
        except: pass

if __name__ == '__main__':
    Thread(target=run).start()
    bot.polling(none_stop=True)
    
