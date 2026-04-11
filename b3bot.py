#Made By @Claxen - Ultimate Flawless Edition

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
import json
import html
import time
import csv
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw, ImageFont 
import io

# ⚙️ CONFIG
BOT_TOKEN = '8217485020:AAHUAQnFeL0hmkXNJ2ZjNddWt3oe-UfLVbc'
ADMIN_GROUP_ID = -1003943618778  
BOT_NAME = "B3 COMPLAINT BOT" 

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "B3 Bot is Online & Safeguarding! 🛡️"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 🗂️ DATABASE & PARAMS
USERS_FILE = 'users.txt'
TICKETS_FILE = 'tickets.json'

tickets_db = {} 
banned_users = set()
user_sessions = {} 
registered_users = set()
user_cooldowns = {} 

URGENT_KEYWORDS = ['fight', 'bully', 'fire', 'khoon', 'marpeet', 'ladiya', 'accident', 'emergency', 'smoke']

# Smart cleaner to remove only specific UI emojis, keeping Hindi/English text safe!
def strip_emojis(text):
    emojis_to_remove = ['🎒', '💼', '🏢', '📌', '✅', '❌', '⏳', '⚙️', '🔴', '⭐']
    for e in emojis_to_remove:
        text = text.replace(e, '')
    return text.strip()

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

# ==========================================
# 🖼️ VIRTUAL TICKET CARD GENERATOR
# ==========================================
def generate_ticket_card(ticket_id, category, user_name):
    W=600; H=350
    bg_color = (22, 27, 34) 
    metallic_border = (48, 54, 61)
    label_color = (139, 148, 158)
    value_color = (201, 209, 217)
    id_accent_color = (248, 81, 73)
    
    img = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(img)
    
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        title_font = ImageFont.truetype(FONT_PATH, 32)
        label_font = ImageFont.truetype(FONT_PATH, 20)
        value_font = ImageFont.truetype(FONT_PATH, 24)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    draw.rectangle([(2,2), (W-3, H-3)], outline=metallic_border, width=5)
    draw.text((W/2, 40), f"🛡️ {BOT_NAME}", fill=(88, 166, 255), font=title_font, anchor="mm")
    draw.line([(50, 70), (W-50, 70)], fill=metallic_border, width=2)
    
    draw.text((70, 110), "TICKET ID:", fill=label_color, font=label_font)
    draw.text((220, 108), ticket_id, fill=id_accent_color, font=value_font)
    draw.text((70, 170), "Category:", fill=label_color, font=label_font)
    draw.text((220, 168), strip_emojis(category), fill=value_color, font=value_font)
    draw.text((70, 230), "Issued To:", fill=label_color, font=label_font)
    draw.text((220, 228), user_name, fill=value_color, font=value_font)
    
    draw.line([(50, 280), (W-50, 280)], fill=metallic_border, width=2)
    draw.text((W/2, 310), f"Powered by Claxen Systems • Render API", fill=label_color, font=label_font, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ==========================================
# ⏱️ AUTO-PURGE (BURN) LOGIC THREAD
# ==========================================
def purge_old_tickets_daemon():
    while True:
        time.sleep(3600) 
        current_time = time.time()
        PURGE_AFTER_SECONDS = 7 * 24 * 60 * 60 
        changed = False
        for tid, d in list(tickets_db.items()):
            if 'resolved_at' in d:
                time_passed = current_time - d['resolved_at']
                if time_passed > PURGE_AFTER_SECONDS:
                    del tickets_db[tid]
                    changed = True
                    try: bot.send_message(ADMIN_GROUP_ID, f"🚮 <b>Memory Optimized:</b> Ticket {tid} has been auto-purged.", parse_mode="HTML")
                    except: pass
        if changed: save_tickets()

# ==========================================
# 🛡️ TELEGRAM COMMANDS & LOGIC
# ==========================================
@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def handle_banned(message):
    bot.reply_to(message, "🛑 <b>ACCESS DENIED</b>\nYou are blacklisted.", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    if uid not in registered_users:
        registered_users.add(uid)
        with open(USERS_FILE, 'a') as f: f.write(f"{uid}\n")
    user_sessions[uid] = {'name': message.from_user.first_name}
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="l_en"), InlineKeyboardButton("🇮🇳 हिंदी", callback_data="l_hi"))
    bot.send_message(uid, f"🏫 ✨ <b>Welcome to {BOT_NAME}</b> ✨ 🏫\n\n🌐 Choose Language / भाषा चुनें 🗣️:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    uid = message.chat.id
    if uid == ADMIN_GROUP_ID:
        admin_help = (
            "👑 <b>ADMIN COMMANDS</b>\n━━━━━━━━━━━━━━\n"
            "📊 /stats - Live Data\n"
            "📢 /broadcast &lt;msg&gt; - Push Alert\n"
            "📁 /report - HTML Dashboard\n"
            "📄 /export - Download Excel/CSV\n"
            "🔓 /unban &lt;ID&gt; - Unblock User"
        )
        return bot.reply_to(message, admin_help, parse_mode="HTML")
    
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    help_txt = "🛠 <b>MENU</b>\n🚀 /start\n🔎 /status &lt;ID&gt;\n🗑️ /delete &lt;ID&gt;" if lang == 'en' else "🛠 <b>सहायता</b>\n🚀 /start\n🔎 /status &lt;ID&gt;\n🗑️ /delete &lt;ID&gt;"
    bot.reply_to(message, help_txt, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith('l_'))
def set_lang(call):
    uid = call.message.chat.id
    lang = call.data.split('_')[1]
    user_sessions[uid]['lang'] = lang
    
    markup = InlineKeyboardMarkup(row_width=1)
    cats = ["🎒 Student Dispute", "💼 Staff Issue", "🏢 Infrastructure", "📌 Other"] if lang == 'en' else ["🎒 छात्र विवाद", "💼 स्टाफ समस्या", "🏢 प्रॉपर्टी", "📌 अन्य"]
    for i, cat in enumerate(["Student", "Staff", "Infra", "Other"]):
        markup.add(InlineKeyboardButton(cats[i], callback_data=f"c_{cat}"))
    
    txt = "📂 Select Category:" if lang == 'en' else "📂 कैटेगरी चुनें:"
    bot.edit_message_text(txt, uid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def ask_text(call):
    uid = call.message.chat.id
    user_sessions[uid]['cat'] = call.data.split('_')[1]
    lang = user_sessions[uid].get('lang', 'en')
    
    txt = "✍️ Type your complaint details:" if lang == 'en' else "✍️ अपनी शिकायत विस्तार से लिखें:"
    bot.edit_message_text(txt, uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    current_time = time.time()
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    
    if uid in user_cooldowns:
        time_passed = current_time - user_cooldowns[uid]
        if time_passed < 300:
            remaining = int((300 - time_passed) / 60)
            wait_msg = f"⏳ <b>Cooldown Active!</b>\nPlease wait {remaining} more minutes." if lang == 'en' else f"⏳ <b>कृपया प्रतीक्षा करें!</b>\nअगली शिकायत के लिए {remaining} मिनट रुकें।"
            return bot.reply_to(message, wait_msg, parse_mode="HTML")

    if is_abusive(message.text):
        bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>ABUSE LOG:</b> {uid}\nContent: {message.text}", parse_mode="HTML")
        warn = "⚠️ <b>Warning:</b> Inappropriate language is not allowed!" if lang == 'en' else "⚠️ <b>चेतावनी:</b> आपत्तिजनक भाषा का प्रयोग वर्जित है!"
        return bot.reply_to(message, warn, parse_mode="HTML")

    user_sessions[uid]['text'] = html.escape(message.text)
    user_cooldowns[uid] = current_time
    
    btn1 = "🕵️ Anonymous" if lang == 'en' else "🕵️ गुप्त (Anonymous)"
    btn2 = "👤 With Name" if lang == 'en' else "👤 नाम के साथ"
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton(btn1, callback_data="s_anon"), InlineKeyboardButton(btn2, callback_data="s_name"))
    
    p_txt = "🛡 Privacy Mode:" if lang == 'en' else "🛡 प्राइवेसी मोड चुनें:"
    bot.send_message(uid, p_txt, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['s_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    data = user_sessions.get(uid)
    tid = f"T{random.randint(1000, 9999)}"
    identity = "Anonymous 🕵️‍♂️" if call.data == 's_anon' else f"{html.escape(data['name'])} 👤"
    PIL_identity = "Anonymous" if call.data == 's_anon' else data['name']
    
    priority_label = "🆕 Unread"
    alert_prefix = "🚨"
    for kw in URGENT_KEYWORDS:
        if kw in data['text'].lower():
            priority_label = "🔴 URGENT / RED ALERT"
            alert_prefix = "🔥 <b>[URGENT]</b>"
            break

    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{uid}")
    )
    
    admin_msg = bot.send_message(ADMIN_GROUP_ID, f"{alert_prefix} <b>NEW TICKET: {tid}</b>\nFrom: {identity}\nIssue: <i>{data['text']}</i>\nStatus: <b>{priority_label}</b>", reply_markup=markup, parse_mode="HTML")
    
    tickets_db[tid] = {'uid': uid, 'text': data['text'], 'status': priority_label, 'cat': data['cat'], 'lang': data['lang'], 'admin_msg_id': admin_msg.message_id}
    save_tickets()
    
    if data['lang'] == 'en':
        conf_msg = f"✅ <b>SUBMITTED!</b>\nYour ID: <code>{tid}</code>\n📝 Check progress using /status {tid}." 
    else:
        conf_msg = f"✅ <b>भेज दिया!</b>\nटिकट ID: <code>{tid}</code>\n📝 प्रोग्रेस देखें /status {tid} से।"
        
    id_card_photo = generate_ticket_card(tid, data['cat'], PIL_identity)
    bot.send_photo(uid, id_card_photo, caption=conf_msg, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def check_status(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    args = message.text.split()
    
    if len(args) < 2: 
        err = "⚠️ Usage: <code>/status T1234</code>" if lang == 'en' else "⚠️ ऐसे लिखें: <code>/status T1234</code>"
        return bot.reply_to(message, err, parse_mode="HTML")
        
    tid = args[1].upper()
    if tid in tickets_db:
        rate = f"\n⭐ Rating: {tickets_db[tid]['rating']}/5" if 'rating' in tickets_db[tid] else ""
        txt = f"🎫 <b>{tid} Status:</b> {tickets_db[tid]['status']}{rate}" if lang == 'en' else f"🎫 <b>{tid} स्टेटस:</b> {tickets_db[tid]['status']}{rate}"
        bot.reply_to(message, txt, parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Not Found." if lang == 'en' else "❌ टिकट नहीं मिला।")

@bot.message_handler(commands=['delete'])
def delete_ticket(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    args = message.text.split()
    
    if len(args) < 2: 
        err = "⚠️ Usage: <code>/delete T1234</code>" if lang == 'en' else "⚠️ ऐसे लिखें: <code>/delete T1234</code>"
        return bot.reply_to(message, err, parse_mode="HTML")
        
    tid = args[1].upper()
    if tid in tickets_db and tickets_db[tid]['uid'] == uid:
        mid = tickets_db[tid].get('admin_msg_id')
        del tickets_db[tid]
        save_tickets()
        bot.reply_to(message, "🗑️ <b>Deleted.</b>" if lang == 'en' else "🗑️ <b>डिलीट कर दिया गया।</b>", parse_mode="HTML")
        if mid:
            try: bot.delete_message(ADMIN_GROUP_ID, mid)
            except: pass
    else:
        bot.reply_to(message, "❌ Denied." if lang == 'en' else "❌ अनुमति नहीं है या टिकट नहीं मिला।")

@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    ratings = [d['rating'] for d in tickets_db.values() if 'rating' in d]
    avg = f"{round(sum(ratings)/len(ratings), 1)} ⭐" if ratings else "No Ratings Yet"
    bot.reply_to(message, f"📊 <b>CORE ANALYTICS</b>\n━━━━━━━━━━━━━━\n📝 Tickets: <b>{len(tickets_db)}</b>\n👥 Users: <b>{len(registered_users)}</b>\n📈 Avg Trust Score: <b>{avg}</b>", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast(message):
    msg = message.text.split(' ', 1)
    if len(msg) < 2: 
        return bot.reply_to(message, "⚠️ Usage: <code>/broadcast Hello everyone!</code>", parse_mode="HTML")
    for u in list(registered_users):
        try: bot.send_message(u, f"📢 <b>ADMIN ANNOUNCEMENT</b>\n━━━━━━━━━━━━━━\n{msg[1]}", parse_mode="HTML")
        except: pass
    bot.reply_to(message, "✅ Broadcast Sent.")

@bot.message_handler(commands=['unban'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def unban(message):
    args = message.text.split()
    if len(args) < 2: 
        return bot.reply_to(message, "⚠️ Usage: <code>/unban 123456789</code>", parse_mode="HTML")
    try:
        uid = int(args[1])
        if uid in banned_users: 
            banned_users.remove(uid)
            bot.reply_to(message, f"✅ User {uid} Unbanned.")
    except: pass

@bot.message_handler(commands=['export'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def export_csv(message):
    fn = "B3_Official_Records.csv"
    with open(fn, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Ticket ID', 'Category', 'Status', 'User Rating (Out of 5)', 'Complaint Details'])
        for tid, d in tickets_db.items():
            rate = f"{d['rating']}" if 'rating' in d else "Not Rated"
            writer.writerow([tid, strip_emojis(d['cat']), strip_emojis(d['status']), rate, d['text']])
    with open(fn, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f, caption="📄 Official Excel/CSV Records Generated")
    os.remove(fn)

@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def report(message):
    fn = "B3_Audit_Report.html"
    colors = {'Solved': '#2ea043', 'Rejected': '#f85149', 'Working': '#d29922', 'Pending': '#8b949e', 'Unread': '#58a6ff', 'URGENT / RED ALERT': '#ff4444'}
    ratings = [d['rating'] for d in tickets_db.values() if 'rating' in d]
    avg = f"{round(sum(ratings)/len(ratings), 1)} / 5" if ratings else "N/A"
    
    html_c = f"<html><head><style>body{{background:#0d1117;color:#c9d1d9;font-family:sans-serif;padding:20px;}}h1{{text-align:center;color:#58a6ff;margin-bottom:5px;}}.trust-score{{text-align:center;color:#d29922;font-size:16px;margin-bottom:20px;font-weight:bold;}}table{{width:100%;border-collapse:collapse;margin-top:20px;}}th,td{{padding:12px;border:1px solid #30363d;text-align:left;}}th{{background:#21262d;color:#8b949e;text-transform:uppercase;font-size:12px;}}.badge{{padding:4px 8px;border-radius:4px;color:white;font-weight:bold;font-size:11px;}}</style></head><body><h1>🛡️ {BOT_NAME} DASHBOARD </h1><div class='trust-score'>School Safety Index: {avg}</div><table><tr><th>ID</th><th>Category</th><th>Status</th><th>Rating</th><th>Complaint</th></tr>"
    
    for tid, d in tickets_db.items():
        st = strip_emojis(d['status'])
        color_key = next((k for k in colors if k in st), 'Unread')
        rate = f"{d['rating']}/5" if 'rating' in d else "-"
        html_c += f"<tr><td style='color:#f85149; font-family:monospace;'>{tid}</td><td>{strip_emojis(d['cat'])}</td><td><span class='badge' style='background:{colors[color_key]};'>{st.upper()}</span></td><td>{rate}</td><td>{d['text']}</td></tr>"
    html_c += "</table><p style='text-align:center; color:#8b949e;'>Generated by Claxen Systems Audit Engine</p></body></html>"
    
    with open(fn, 'w', encoding='utf-8') as f: f.write(html_c)
    with open(fn, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f, caption="📊 Professional Audit Dashboard (Emoji-Free)")
    os.remove(fn)

@bot.callback_query_handler(func=lambda c: c.data.startswith('rate_'))
def handle_rating(call):
    _, stars, tid = call.data.split('_')
    if tid in tickets_db:
        tickets_db[tid]['rating'] = int(stars)
        save_tickets()
        lang = tickets_db[tid].get('lang', 'en')
        ty_msg = f"Thank you! You rated: {'⭐'*int(stars)}" if lang == 'en' else f"धन्यवाद! आपकी रेटिंग: {'⭐'*int(stars)}"
        bot.edit_message_text(ty_msg, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('st_') or c.data.startswith('admin_ban_'))
def handle_admin(call):
    if 'ban' in call.data:
        uid = int(call.data.split('_')[2]); banned_users.add(uid)
        return bot.answer_callback_query(call.id, "User Banned! 🚫")
    
    _, action, sid, tid = call.data.split('_')
    
    # 🌟 MAXIMUM DETAILED PROFESSIONAL MESSAGES
    status_map = {
        'rej': {'label': '❌ Rejected', 'en': f"❌ <b>TICKET REJECTED ({tid})</b>\nUnfortunately, your complaint has been officially rejected by the school administration. Possible reasons include insufficient information provided, or the issue not violating any school policies. If you think this is a mistake, please submit a new detailed report.", 'hi': f"❌ <b>रिपोर्ट खारिज ({tid})</b>\nक्षमा करें, स्कूल प्रशासन ने आपकी शिकायत को आधिकारिक तौर पर खारिज कर दिया है। अधूरी जानकारी या स्कूल के नियमों का उल्लंघन नहीं होना इसका कारण हो सकता है। कृपया नई रिपोर्ट दर्ज करें।"},
        'pen': {'label': '⏳ Pending', 'en': f"⏳ <b>TICKET PENDING ({tid})</b>\nYour report has been successfully placed in the pending queue. The administration is reviewing complaints sequentially. Please be patient, we will get to your issue shortly.", 'hi': f"⏳ <b>प्रोग्रेस अपडेट ({tid})</b>\nआपकी रिपोर्ट अभी पेंडिंग कतार में सुरक्षित है। हमारी टीम शिकायतों की क्रमबद्ध समीक्षा कर रही है। कृपया धैर्य रखें, हम जल्द ही आपकी समस्या देखेंगे।"},
        'wrk': {'label': '⚙️ Working', 'en': f"⚙️ <b>INVESTIGATION STARTED ({tid})</b>\nExcellent news! The school administration has officially started an investigation based on your report. We are actively working on the ground to fix this issue as soon as possible.", 'hi': f"⚙️ <b>कार्यवाही शुरू ({tid})</b>\nअच्छी खबर! स्कूल प्रशासन ने आपकी शिकायत पर आधिकारिक रूप से जांच और कार्यवाही शुरू कर दी है। हम इस समस्या को जल्द से जल्द सुलझाने के लिए काम कर रहे हैं।"},
        'sol': {'label': '✅ Solved', 'en': f"✅ <b>ISSUE RESOLVED ({tid})</b>\nThe school administration has successfully investigated and resolved your complaint. Thank you for helping us make our school environment safer and better!\n\n<i>Please rate your overall experience below:</i>", 'hi': f"✅ <b>समस्या का समाधान! ({tid})</b>\nस्कूल प्रशासन ने आपकी शिकायत की सफलतापूर्वक जांच कर उसका समाधान कर लिया है। स्कूल को सुरक्षित और बेहतर बनाने में हमारी मदद करने के लिए धन्यवाद!\n\n<i>कृपया अपने अनुभव की रेटिंग दें:</i>"}
    }
    
    current = status_map.get(action)
    if tid in tickets_db:
        if action == 'sol':
            tickets_db[tid]['resolved_at'] = time.time()
            try: bot.send_message(ADMIN_GROUP_ID, f"🚮 <b>Burn Audit Log Activated:</b> Ticket {tid} will be permanently removed in 7 days.", parse_mode="HTML")
  
