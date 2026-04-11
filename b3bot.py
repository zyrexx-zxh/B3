#Made By @Claxen - Arcvium Network Final Safeguarding System
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random, os, json, html, time, csv, io, re
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw, ImageFont

# ⚙️ CONFIGURATION
BOT_TOKEN = '8217485020:AAHUAQnFeL0hmkXNJ2ZjNddWt3oe-UfLVbc'
ADMIN_GROUP_ID = -1003943618778
BOT_NAME = "B3 COMPLAINT BOT"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home(): 
    return "<h1>B3 Safeguarding System is Online!</h1><p>Powered by Claxen Systems</p>"

def run_web(): 
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 🗂️ DATABASE & LOGIC
TICKETS_FILE = 'tickets.json'
USERS_FILE = 'users.txt'
tickets_db = {}
registered_users = set()
banned_users = set()
user_sessions = {}
user_cooldowns = {}
URGENT_KEYWORDS = ['fight', 'bully', 'fire', 'khoon', 'marpeet', 'ladiya', 'accident', 'emergency', 'smoke']
BAD_WORDS = ['bc', 'mc', 'tmkc', 'rndi', 'randi', 'chod', 'lund', 'land', 'bhosda']

# --- HELPER FUNCTIONS ---
def is_abusive(text):
    t = text.lower()
    return any(word in t for word in BAD_WORDS)

def strip_emojis(text):
    for e in ['🎒', '💼', '🏢', '📌', '✅', '❌', '⏳', '⚙️', '🔴', '⭐']:
        text = text.replace(e, '')
    return text.strip()

def load_data():
    global tickets_db, registered_users
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, 'r', encoding='utf-8') as f: tickets_db = json.load(f)
        except Exception: pass
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): registered_users.add(int(line.strip()))
        except Exception: pass

def save_tickets():
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f: json.dump(tickets_db, f)

load_data()

# ==========================================
# 🖼️ VIRTUAL ID CARD GENERATOR
# ==========================================
def generate_ticket_card(ticket_id, category, user_name):
    W, H = 600, 350
    img = Image.new('RGB', (W, H), (22, 27, 34))
    draw = ImageDraw.Draw(img)
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        t_font = ImageFont.truetype(FONT_PATH, 32)
        l_font = ImageFont.truetype(FONT_PATH, 20)
        v_font = ImageFont.truetype(FONT_PATH, 24)
    except:
        t_font = l_font = v_font = ImageFont.load_default()
    
    draw.rectangle([(2,2), (W-3, H-3)], outline=(48, 54, 61), width=5)
    draw.text((W/2, 45), f"🛡️ {BOT_NAME}", fill=(88, 166, 255), font=t_font, anchor="mm")
    draw.line([(50, 80), (W-50, 80)], fill=(48, 54, 61), width=2)
    draw.text((70, 120), "TICKET ID:", fill=(139, 148, 158), font=l_font)
    draw.text((220, 118), ticket_id, fill=(248, 81, 73), font=v_font)
    draw.text((70, 180), "Category:", fill=(139, 148, 158), font=l_font)
    draw.text((220, 178), strip_emojis(category), fill=(201, 209, 217), font=v_font)
    draw.text((70, 240), "Issued To:", fill=(139, 148, 158), font=l_font)
    draw.text((220, 238), user_name, fill=(201, 209, 217), font=v_font)
    draw.text((W/2, 315), "Powered by Arcvium Network", fill=(139, 148, 158), font=l_font, anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# ==========================================
# ⏱️ AUTO-BURN DAEMON (7 DAYS)
# ==========================================
def purge_old_tickets_daemon():
    while True:
        time.sleep(3600)
        now = time.time()
        changed = False
        for tid, d in list(tickets_db.items()):
            if 'resolved_at' in d and now - d['resolved_at'] > 604800:
                del tickets_db[tid]
                changed = True
        if changed: save_tickets()

# ==========================================
# 🛡️ MAIN HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    if uid not in registered_users:
        registered_users.add(uid)
        with open(USERS_FILE, 'a') as f: f.write(f"{uid}\n")
    user_sessions[uid] = {'name': message.from_user.first_name}
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="l_en"), InlineKeyboardButton("🇮🇳 हिंदी", callback_data="l_hi"))
    bot.send_message(uid, f"🏫 ✨ <b>Welcome to {BOT_NAME}</b> ✨ 🏫\n\nChoose Language / भाषा चुनें:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    uid = message.chat.id
    if uid == ADMIN_GROUP_ID:
        msg = "👑 <b>ADMIN COMMANDS</b>\n/stats - Live Analytics\n/broadcast - Push Announcement\n/report - HTML Dashboard\n/export - Excel Record\n/unban - Unblock User"
    else:
        lang = user_sessions.get(uid, {}).get('lang', 'en')
        msg = "🛠 <b>MENU</b>\n🚀 /start\n🔎 /status ID\n🗑️ /delete ID" if lang == 'en' else "🛠 <b>सहायता मेनू</b>\n🚀 /start\n🔎 /status ID\n🗑️ /delete ID"
    bot.reply_to(message, msg, parse_mode="HTML")

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
    lang = user_sessions[uid].get('lang', 'en')
    bot.edit_message_text("✍️ Type complaint details:" if lang == 'en' else "✍️ अपनी शिकायत विस्तार से लिखें:", uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    if time.time() - user_cooldowns.get(uid, 0) < 300:
        return bot.reply_to(message, "⏳ Wait 5 mins!" if lang == 'en' else "⏳ 5 मिनट रुकें!")
    if is_abusive(message.text):
        return bot.reply_to(message, "⚠️ Watch your language!" if lang == 'en' else "⚠️ भाषा का ध्यान रखें!")
    
    user_sessions[uid]['text'] = html.escape(message.text)
    user_cooldowns[uid] = time.time()
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🕵️ Anonymous", callback_data="s_anon"), InlineKeyboardButton("👤 With Name", callback_data="s_name"))
    bot.send_message(uid, "🛡 Privacy Mode:" if lang == 'en' else "🛡 प्राइवेसी मोड:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['s_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    data = user_sessions.get(uid)
    tid = f"T{random.randint(1000, 9999)}"
    PIL_name = "Anonymous" if call.data == 's_anon' else data['name']
    
    priority = "🆕 Unread"
    alert = "🚨"
    for kw in URGENT_KEYWORDS:
        if kw in data['text'].lower(): 
            priority = "🔴 URGENT"
            alert = "🔥 <b>[URGENT]</b>"
            break
    
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban", callback_data=f"admin_ban_{uid}")
    )
    admin_msg = bot.send_message(ADMIN_GROUP_ID, f"{alert} <b>TICKET: {tid}</b>\nFrom: {PIL_name}\nIssue: {data['text']}\nStatus: {priority}", reply_markup=markup, parse_mode="HTML")
    tickets_db[tid] = {'uid': uid, 'text': data['text'], 'status': priority, 'cat': data['cat'], 'lang': data['lang'], 'admin_msg_id': admin_msg.message_id}
    save_tickets()
    
    conf = f"✅ <b>SENT!</b> ID: {tid}" if data['lang'] == 'en' else f"✅ <b>भेज दिया!</b> ID: {tid}"
    card = generate_ticket_card(tid, data['cat'], PIL_name)
    bot.send_photo(uid, card, caption=conf, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def check_status(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Usage: /status T1234")
    tid = args[1].upper()
    if tid in tickets_db:
        rate = f"\n⭐ Rating: {tickets_db[tid]['rating']}/5" if 'rating' in tickets_db[tid] else ""
        bot.reply_to(message, f"🎫 <b>{tid} Status:</b> {tickets_db[tid]['status']}{rate}", parse_mode="HTML")

@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    ratings = [d['rating'] for d in tickets_db.values() if 'rating' in d]
    avg = f"{round(sum(ratings)/len(ratings), 1)} ⭐" if ratings else "N/A"
    bot.reply_to(message, f"📊 <b>STATS</b>\nTickets: {len(tickets_db)}\nUsers: {len(registered_users)}\nAvg Rating: {avg}", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast(message):
    msg = message.text.split(' ', 1)
    if len(msg) < 2: return
    for u in list(registered_users):
        try: bot.send_message(u, f"📢 <b>ADMIN ANNOUNCEMENT</b>\n{msg[1]}", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['export'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def export_csv(message):
    fn = "B3_Official.csv"
    with open(fn, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Cat', 'Status', 'Rating', 'Complaint'])
        for tid, d in tickets_db.items():
            writer.writerow([tid, strip_emojis(d['cat']), strip_emojis(d['status']), d.get('rating', '-'), d['text']])
    with open(fn, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f)
    os.remove(fn)

@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def report(message):
    fn = "B3_Audit.html"
    colors = {'Solved': '#2ea043', 'Rejected': '#f85149', 'Working': '#d29922', 'Pending': '#8b949e', 'Unread': '#58a6ff', 'URGENT': '#ff4444'}
    ratings = [d['rating'] for d in tickets_db.values() if 'rating' in d]
    avg = f"{round(sum(ratings)/len(ratings), 1)} / 5" if ratings else "N/A"
    html_c = f"<html><head><meta charset='UTF-8'><style>body{{background:#0d1117;color:#c9d1d9;font-family:sans-serif;}}table{{width:100%;border-collapse:collapse;}}th,td{{padding:12px;border:1px solid #30363d;}}th{{background:#21262d;}}.badge{{padding:4px;border-radius:4px;color:white;}}</style></head><body><h1>🛡️ {BOT_NAME} AUDIT </h1><h3>Safety Index: {avg}</h3><table><tr><th>ID</th><th>Status</th><th>Rating</th><th>Complaint</th></tr>"
    for tid, d in tickets_db.items():
        st = strip_emojis(d['status'])
        c_key = next((k for k in colors if k in st), 'Unread')
        html_c += f"<tr><td>{tid}</td><td><span class='badge' style='background:{colors[c_key]};'>{st.upper()}</span></td><td>{d.get('rating','-')}</td><td>{d['text']}</td></tr>"
    html_c += "</table></body></html>"
    with open(fn, 'w', encoding='utf-8') as f: f.write(html_c)
    with open(fn, 'rb') as f: bot.send_document(ADMIN_GROUP_ID, f)
    os.remove(fn)

@bot.callback_query_handler(func=lambda c: c.data.startswith('rate_'))
def handle_rate(call):
    _, stars, tid = call.data.split('_')
    if tid in tickets_db:
        tickets_db[tid]['rating'] = int(stars)
        save_tickets()
        bot.edit_message_text(f"Thank you! You gave {stars}⭐", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('st_') or c.data.startswith('admin_ban_'))
def handle_admin(call):
    if 'ban' in call.data: return bot.answer_callback_query(call.id, "Banned!")
    _, act, sid, tid = call.data.split('_')
    
    # Text mapping safe from line breaks
    m_en_rej = "❌ <b>TICKET REJECTED</b>\nComplaint rejected by administration. Possible reasons: insufficient info or no policy violation."
    m_hi_rej = "❌ <b>रिपोर्ट खारिज</b>\nअधूरी जानकारी या नियमों का उल्लंघन नहीं होने के कारण शिकायत खारिज कर दी गई है।"
    
    m_en_pen = "⏳ <b>TICKET PENDING</b>\nPlaced in queue for sequential review. Please wait."
    m_hi_pen = "⏳ <b>पेंडिंग कतार</b>\nआपकी रिपोर्ट समीक्षा के लिए कतार में है।"
    
    m_en_wrk = "⚙️ <b>INVESTIGATION STARTED</b>\nAdministration has started active investigation on the ground."
    m_hi_wrk = "⚙️ <b>कार्यवाही शुरू</b>\nप्रशासन ने जांच शुरू कर दी है।"
    
    m_en_sol = "✅ <b>ISSUE RESOLVED</b>\nResolved! Thank you for B3 safety.\nPlease rate your experience:"
    m_hi_sol = "✅ <b>समाधान हो गया!</b>\nB3 को सुरक्षित बनाने के लिए धन्यवाद।\nकृपया रेटिंग दें:"
    
    s_map = {
        'rej': ('❌ Rejected', m_en_rej, m_hi_rej),
        'pen': ('⏳ Pending', m_en_pen, m_hi_pen),
        'wrk': ('⚙️ Working', m_en_wrk, m_hi_wrk),
        'sol': ('✅ Solved', m_en_sol, m_hi_sol)
    }
    
    label, m_en, m_hi = s_map[act]
    if tid in tickets_db:
        if act == 'sol': tickets_db[tid]['resolved_at'] = time.time()
        tickets_db[tid]['status'] = label
        save_tickets()
        bot.edit_message_text(f"Ticket {tid} Status: {label}", call.message.chat.id, call.message.message_id)
        
        markup = None
        if act == 'sol':
            markup = InlineKeyboardMarkup(row_width=5)
            markup.add(*[InlineKeyboardButton(f"{i}⭐", callback_data=f"rate_{i}_{tid}") for i in range(1,6)])
        
        msg = m_en if tickets_db[tid]['lang'] == 'en' else m_hi
        try: bot.send_message(int(sid), f"🎫 <b>Update {tid}:</b>\n{msg}", parse_mode="HTML", reply_markup=markup)
        except: pass

if __name__ == '__main__':
    Thread(target=run_web).start()
    Thread(target=purge_old_tickets_daemon).start()
    bot.polling(none_stop=True)
    
