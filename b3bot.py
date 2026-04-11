# Made By @Claxen - Arcvium Network Final Safeguarding System
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
import json
import html
import time
import csv
import io
import re
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
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

# ==========================================
# 🗂️ DATABASE & LOGIC PARAMS
# ==========================================
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
    for word in BAD_WORDS:
        if word in t:
            return True
    return False

def strip_emojis(text):
    emojis_to_remove = ['🎒', '💼', '🏢', '📌', '✅', '❌', '⏳', '⚙️', '🔴', '⭐']
    for emoji in emojis_to_remove:
        text = text.replace(emoji, '')
    return text.strip()

def load_data():
    global tickets_db, registered_users
    
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, 'r', encoding='utf-8') as f: 
                tickets_db = json.load(f)
        except Exception as e: 
            print(f"Error loading tickets: {e}")
            
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): 
                        registered_users.add(int(line.strip()))
        except Exception as e: 
            print(f"Error loading users: {e}")

def save_tickets():
    try:
        with open(TICKETS_FILE, 'w', encoding='utf-8') as f: 
            json.dump(tickets_db, f)
    except Exception as e:
        print(f"Error saving tickets: {e}")

load_data()

# ==========================================
# 🖼️ VIRTUAL ID CARD GENERATOR
# ==========================================
def generate_ticket_card(ticket_id, category, user_name):
    W = 600
    H = 350
    img = Image.new('RGB', (W, H), (22, 27, 34))
    draw = ImageDraw.Draw(img)
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        title_font = ImageFont.truetype(FONT_PATH, 32)
        label_font = ImageFont.truetype(FONT_PATH, 20)
        value_font = ImageFont.truetype(FONT_PATH, 24)
    except Exception:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    # Border
    draw.rectangle([(2,2), (W-3, H-3)], outline=(48, 54, 61), width=5)
    
    # Header
    draw.text((W/2, 45), f"🛡️ {BOT_NAME}", fill=(88, 166, 255), font=title_font, anchor="mm")
    draw.line([(50, 80), (W-50, 80)], fill=(48, 54, 61), width=2)
    
    # Body Details
    draw.text((70, 120), "TICKET ID:", fill=(139, 148, 158), font=label_font)
    draw.text((220, 118), ticket_id, fill=(248, 81, 73), font=value_font)
    
    draw.text((70, 180), "Category:", fill=(139, 148, 158), font=label_font)
    draw.text((220, 178), strip_emojis(category), fill=(201, 209, 217), font=value_font)
    
    draw.text((70, 240), "Issued To:", fill=(139, 148, 158), font=label_font)
    draw.text((220, 238), user_name, fill=(201, 209, 217), font=value_font)
    
    # Footer
    draw.text((W/2, 315), "Powered by Arcvium Network", fill=(139, 148, 158), font=label_font, anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# ==========================================
# ⏱️ AUTO-BURN DAEMON (7 DAYS)
# ==========================================
def purge_old_tickets_daemon():
    while True:
        time.sleep(3600)
        current_time = time.time()
        changed = False
        
        for tid, data in list(tickets_db.items()):
            if 'resolved_at' in data:
                time_passed = current_time - data['resolved_at']
                # 7 Days in seconds = 604800
                if time_passed > 604800:
                    del tickets_db[tid]
                    changed = True
                    try:
                        bot.send_message(ADMIN_GROUP_ID, f"🚮 <b>Memory Optimized:</b> Ticket {tid} has been auto-purged.", parse_mode="HTML")
                    except Exception:
                        pass
                        
        if changed: 
            save_tickets()

# ==========================================
# 🛡️ MAIN BOT HANDLERS
# ==========================================

@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def handle_banned(message):
    bot.reply_to(message, "🛑 <b>ACCESS DENIED</b>\nYou are blacklisted.", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    
    if uid not in registered_users:
        registered_users.add(uid)
        try:
            with open(USERS_FILE, 'a', encoding='utf-8') as f: 
                f.write(f"{uid}\n")
        except Exception as e:
            print(f"Error saving user: {e}")
            
    user_sessions[uid] = {'name': message.from_user.first_name}
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="l_en"))
    markup.add(InlineKeyboardButton("🇮🇳 हिंदी", callback_data="l_hi"))
    
    welcome_text = f"🏫 ✨ <b>Welcome to {BOT_NAME}</b> ✨ 🏫\n\nChoose Language / भाषा चुनें:"
    bot.send_message(uid, welcome_text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    uid = message.chat.id
    
    if uid == ADMIN_GROUP_ID:
        admin_msg = (
            "👑 <b>ADMIN COMMANDS</b>\n━━━━━━━━━━━━━━\n"
            "📊 /stats - Live Analytics\n"
            "📢 /broadcast &lt;msg&gt; - Push Announcement\n"
            "📁 /report - HTML Dashboard\n"
            "📄 /export - Excel Record\n"
            "🔓 /unban &lt;ID&gt; - Unblock User"
        )
        bot.reply_to(message, admin_msg, parse_mode="HTML")
    else:
        lang = user_sessions.get(uid, {}).get('lang', 'en')
        if lang == 'en':
            user_msg = "🛠 <b>MENU</b>\n🚀 /start - New Report\n🔎 /status &lt;ID&gt; - Check Progress\n🗑️ /delete &lt;ID&gt; - Remove Report"
        else:
            user_msg = "🛠 <b>सहायता मेनू</b>\n🚀 /start - नई रिपोर्ट\n🔎 /status &lt;ID&gt; - स्टेटस जांचें\n🗑️ /delete &lt;ID&gt; - रिपोर्ट हटाएं"
        bot.reply_to(message, user_msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith('l_'))
def set_lang(call):
    uid = call.message.chat.id
    lang = call.data.split('_')[1]
    
    if uid not in user_sessions:
        user_sessions[uid] = {'name': call.message.chat.first_name}
        
    user_sessions[uid]['lang'] = lang
    
    markup = InlineKeyboardMarkup(row_width=1)
    if lang == 'en':
        cats = ["🎒 Student Dispute", "💼 Staff Issue", "🏢 Infrastructure", "📌 Other"]
        header_text = "📂 Select Category:"
    else:
        cats = ["🎒 छात्र विवाद", "💼 स्टाफ समस्या", "🏢 प्रॉपर्टी", "📌 अन्य"]
        header_text = "📂 कैटेगरी चुनें:"
        
    callbacks = ["Student", "Staff", "Infra", "Other"]
    
    for i in range(len(cats)):
        markup.add(InlineKeyboardButton(cats[i], callback_data=f"c_{callbacks[i]}"))
        
    bot.edit_message_text(header_text, uid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def ask_text(call):
    uid = call.message.chat.id
    category_data = call.data.split('_')[1]
    
    if uid not in user_sessions:
        return
        
    user_sessions[uid]['cat'] = category_data
    lang = user_sessions[uid].get('lang', 'en')
    
    if lang == 'en':
        prompt_text = "✍️ Please type your complaint details in full:"
    else:
        prompt_text = "✍️ कृपया अपनी शिकायत विस्तार से लिखें:"
        
    bot.edit_message_text(prompt_text, uid, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(uid, handle_complaint_text)

def handle_complaint_text(message):
    uid = message.chat.id
    current_time = time.time()
    
    if uid not in user_sessions:
        user_sessions[uid] = {'name': message.from_user.first_name, 'lang': 'en'}
        
    lang = user_sessions[uid].get('lang', 'en')
    
    # Rate Limiting Check (300 seconds = 5 minutes)
    if uid in user_cooldowns:
        time_passed = current_time - user_cooldowns[uid]
        if time_passed < 300:
            remaining_time = int((300 - time_passed) / 60)
            if lang == 'en':
                wait_msg = f"⏳ <b>Cooldown Active!</b>\nPlease wait {remaining_time} more minutes to avoid spam."
            else:
                wait_msg = f"⏳ <b>कृपया प्रतीक्षा करें!</b>\nस्पैम से बचने के लिए {remaining_time} मिनट रुकें।"
            bot.reply_to(message, wait_msg, parse_mode="HTML")
            return
            
    # Abuse Filter Check
    if is_abusive(message.text):
        bot.send_message(ADMIN_GROUP_ID, f"🚨 <b>ABUSE LOG:</b> {uid}\nContent: {message.text}", parse_mode="HTML")
        if lang == 'en':
            warn_msg = "⚠️ <b>Warning:</b> Inappropriate language is strictly prohibited!"
        else:
            warn_msg = "⚠️ <b>चेतावनी:</b> आपत्तिजनक भाषा का प्रयोग सख्त मना है!"
        bot.reply_to(message, warn_msg, parse_mode="HTML")
        return
    
    user_sessions[uid]['text'] = html.escape(message.text)
    user_cooldowns[uid] = current_time
    
    markup = InlineKeyboardMarkup(row_width=2)
    if lang == 'en':
        btn_anon = "🕵️ Anonymous"
        btn_name = "👤 With Name"
        privacy_text = "🛡 Select Privacy Mode:"
    else:
        btn_anon = "🕵️ गुप्त (Anonymous)"
        btn_name = "👤 नाम के साथ"
        privacy_text = "🛡 प्राइवेसी मोड चुनें:"
        
    markup.add(
        InlineKeyboardButton(btn_anon, callback_data="s_anon"), 
        InlineKeyboardButton(btn_name, callback_data="s_name")
    )
    
    bot.send_message(uid, privacy_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ['s_anon', 's_name'])
def final_submit(call):
    uid = call.message.chat.id
    
    if uid not in user_sessions:
        return
        
    data = user_sessions.get(uid)
    tid = f"T{random.randint(1000, 9999)}"
    
    if call.data == 's_anon':
        html_name = "Anonymous 🕵️‍♂️"
        pil_name = "Anonymous"
    else:
        html_name = f"{html.escape(data['name'])} 👤"
        pil_name = data['name']
    
    # AI Priority Check
    priority = "🆕 Unread"
    alert_icon = "🚨"
    for kw in URGENT_KEYWORDS:
        if kw in data['text'].lower():
            priority = "🔴 URGENT / RED ALERT"
            alert_icon = "🔥 <b>[URGENT]</b>"
            break
    
    # Admin Panel Keyboard
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❌ Reject", callback_data=f"st_rej_{uid}_{tid}"),
        InlineKeyboardButton("⏳ Pending", callback_data=f"st_pen_{uid}_{tid}"),
        InlineKeyboardButton("⚙️ Working", callback_data=f"st_wrk_{uid}_{tid}"),
        InlineKeyboardButton("✅ Solved", callback_data=f"st_sol_{uid}_{tid}"),
        InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{uid}")
    )
    
    admin_content = f"{alert_icon} <b>NEW TICKET: {tid}</b>\nFrom: {html_name}\nIssue: <i>{data['text']}</i>\nStatus: <b>{priority}</b>"
    admin_msg = bot.send_message(ADMIN_GROUP_ID, admin_content, reply_markup=markup, parse_mode="HTML")
    
    # Save to Database
    tickets_db[tid] = {
        'uid': uid, 
        'text': data['text'], 
        'status': priority, 
        'cat': data['cat'], 
        'lang': data['lang'], 
        'admin_msg_id': admin_msg.message_id
    }
    save_tickets()
    
    # Send Confirmation and Virtual Card to User
    if data['lang'] == 'en':
        conf_msg = f"✅ <b>SUBMITTED SUCCESSFULLY!</b>\nYour Tracking ID: <code>{tid}</code>\n📝 Check progress anytime using /status {tid}"
    else:
        conf_msg = f"✅ <b>सफलतापूर्वक भेज दिया गया!</b>\nआपकी ट्रैकिंग ID: <code>{tid}</code>\n📝 प्रोग्रेस देखने के लिए /status {tid} का उपयोग करें।"
        
    card_image = generate_ticket_card(tid, data['cat'], pil_name)
    bot.delete_message(uid, call.message.message_id) # Clean up the privacy message
    bot.send_photo(uid, card_image, caption=conf_msg, parse_mode="HTML")

# ==========================================
# 🔎 COMMAND: STATUS
# ==========================================
@bot.message_handler(commands=['status'])
def check_status(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    args = message.text.split()
    
    if len(args) < 2:
        if lang == 'en':
            err_msg = "⚠️ <b>Correct Usage:</b>\n<code>/status T1234</code>"
        else:
            err_msg = "⚠️ <b>सही उपयोग:</b>\n<code>/status T1234</code>"
        bot.reply_to(message, err_msg, parse_mode="HTML")
        return
        
    tid = args[1].upper()
    
    if tid in tickets_db:
        rating_text = ""
        if 'rating' in tickets_db[tid]:
            rating_text = f"\n⭐ User Rating: {tickets_db[tid]['rating']}/5"
            
        if lang == 'en':
            status_reply = f"🎫 <b>Ticket ID:</b> {tid}\n<b>Current Status:</b> {tickets_db[tid]['status']}{rating_text}"
        else:
            status_reply = f"🎫 <b>टिकट ID:</b> {tid}\n<b>वर्तमान स्टेटस:</b> {tickets_db[tid]['status']}{rating_text}"
            
        bot.reply_to(message, status_reply, parse_mode="HTML")
    else:
        if lang == 'en':
            bot.reply_to(message, "❌ Ticket not found. Please check your ID.")
        else:
            bot.reply_to(message, "❌ टिकट नहीं मिला। कृपया अपनी ID जांचें।")

# ==========================================
# 🗑️ COMMAND: DELETE
# ==========================================
@bot.message_handler(commands=['delete'])
def delete_ticket(message):
    uid = message.chat.id
    lang = user_sessions.get(uid, {}).get('lang', 'en')
    args = message.text.split()
    
    if len(args) < 2:
        if lang == 'en':
            err_msg = "⚠️ <b>Correct Usage:</b>\n<code>/delete T1234</code>"
        else:
            err_msg = "⚠️ <b>सही उपयोग:</b>\n<code>/delete T1234</code>"
        bot.reply_to(message, err_msg, parse_mode="HTML")
        return
        
    tid = args[1].upper()
    
    if tid in tickets_db and tickets_db[tid]['uid'] == uid:
        mid = tickets_db[tid].get('admin_msg_id')
        del tickets_db[tid]
        save_tickets()
        
        if lang == 'en':
            bot.reply_to(message, "🗑️ <b>Ticket Deleted Successfully.</b>", parse_mode="HTML")
        else:
            bot.reply_to(message, "🗑️ <b>टिकट सफलतापूर्वक डिलीट कर दिया गया।</b>", parse_mode="HTML")
            
        if mid:
            try: 
                bot.delete_message(ADMIN_GROUP_ID, mid)
            except Exception as e: 
                print(f"Could not delete admin msg: {e}")
    else:
        if lang == 'en':
            bot.reply_to(message, "❌ Access Denied or Ticket Not Found.")
        else:
            bot.reply_to(message, "❌ अनुमति नहीं है या टिकट नहीं मिला।")

# ==========================================
# 📊 COMMAND: STATS (ADMIN)
# ==========================================
@bot.message_handler(commands=['stats'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def show_stats(message):
    ratings_list = []
    for d in tickets_db.values():
        if 'rating' in d:
            ratings_list.append(d['rating'])
            
    if ratings_list:
        average_rating = f"{round(sum(ratings_list)/len(ratings_list), 1)} ⭐"
    else:
        average_rating = "No Ratings Yet"
        
    stats_msg = (
        f"📊 <b>CORE ANALYTICS</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📝 Total Tickets: <b>{len(tickets_db)}</b>\n"
        f"👥 Registered Users: <b>{len(registered_users)}</b>\n"
        f"📈 Avg Trust Score: <b>{average_rating}</b>"
    )
    bot.reply_to(message, stats_msg, parse_mode="HTML")

# ==========================================
# 📢 COMMAND: BROADCAST (ADMIN)
# ==========================================
@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def broadcast(message):
    args = message.text.split(' ', 1)
    
    if len(args) < 2: 
        bot.reply_to(message, "⚠️ <b>Usage:</b>\n<code>/broadcast Hello everyone!</code>", parse_mode="HTML")
        return
        
    broadcast_text = args[1]
    success_count = 0
    
    for user_id in list(registered_users):
        try: 
            bot.send_message(user_id, f"📢 <b>ADMIN ANNOUNCEMENT</b>\n━━━━━━━━━━━━━━\n{broadcast_text}", parse_mode="HTML")
            success_count += 1
        except Exception: 
            pass
            
    bot.reply_to(message, f"✅ Broadcast sent successfully to {success_count} users.")

# ==========================================
# 🔓 COMMAND: UNBAN (ADMIN)
# ==========================================
@bot.message_handler(commands=['unban'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def unban(message):
    args = message.text.split()
    
    if len(args) < 2: 
        bot.reply_to(message, "⚠️ <b>Usage:</b>\n<code>/unban 123456789</code>", parse_mode="HTML")
        return
        
    try:
        target_uid = int(args[1])
        if target_uid in banned_users: 
            banned_users.remove(target_uid)
            bot.reply_to(message, f"✅ User {target_uid} has been Unbanned.")
        else:
            bot.reply_to(message, "ℹ️ User is not banned.")
    except Exception as e: 
        bot.reply_to(message, "❌ Invalid User ID format.")

# ==========================================
# 📄 COMMAND: EXPORT CSV (ADMIN)
# ==========================================
@bot.message_handler(commands=['export'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def export_csv(message):
    filename = "B3_Official.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Ticket ID', 'Category', 'Status', 'User Rating', 'Complaint Details'])
            
            for tid, data in tickets_db.items():
                if 'rating' in data:
                    user_rating = f"{data['rating']}"
                else:
                    user_rating = "Not Rated"
                    
                safe_cat = strip_emojis(data['cat'])
                safe_status = strip_emojis(data['status'])
                
                writer.writerow([tid, safe_cat, safe_status, user_rating, data['text']])
                
        with open(filename, 'rb') as f: 
            bot.send_document(ADMIN_GROUP_ID, f, caption="📄 Official Excel/CSV Records Generated")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating CSV: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
# ==========================================
# 📁 COMMAND: REPORT HTML (ADMIN)
# ==========================================
@bot.message_handler(commands=['report'], func=lambda m: m.chat.id == ADMIN_GROUP_ID)
def report(message):
    filename = "B3_Audit_Report.html"
    colors = {
        'Solved': '#2ea043', 
        'Rejected': '#f85149', 
        'Working': '#d29922', 
        'Pending': '#8b949e', 
        'Unread': '#58a6ff', 
        'URGENT': '#ff4444'
    }
    
    ratings_list = []
    for d in tickets_db.values():
        if 'rating' in d:
            ratings_list.append(d['rating'])
            
    if ratings_list:
        avg_rating = f"{round(sum(ratings_list)/len(ratings_list), 1)} / 5"
    else:
        avg_rating = "N/A"
        
    html_content = f"""
    <html>
    <head>
        <meta charset='UTF-8'>
        <style>
            body {{ background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px; }}
            h1 {{ text-align:center; color:#58a6ff; margin-bottom:5px; }}
            .trust-score {{ text-align:center; color:#d29922; font-size:16px; margin-bottom:20px; font-weight:bold; }}
            table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
            th, td {{ padding:12px; border:1px solid #30363d; text-align:left; }}
            th {{ background:#21262d; color:#8b949e; text-transform:uppercase; font-size:12px; }}
            .badge {{ padding:6px 10px; border-radius:4px; color:white; font-weight:bold; font-size:11px; }}
        </style>
    </head>
    <body>
        <h1>🛡️ {BOT_NAME} AUDIT DASHBOARD</h1>
        <div class='trust-score'>School Safety Index: {avg_rating}</div>
        <table>
            <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Status</th>
                <th>Rating</th>
                <th>Complaint Details</th>
            </tr>
    """
    
    for tid, data in tickets_db.items():
        clean_status = strip_emojis(data['status'])
        clean_cat = strip_emojis(data['cat'])
        
        bg_color = '#58a6ff' # Default Unread
        for key, hexcode in colors.items():
            if key in clean_status:
                bg_color = hexcode
                break
                
        if 'rating' in data:
            rating_display = f"{data['rating']}/5"
        else:
            rating_display = "-"
            
        html_content += f"""
            <tr>
                <td style='color:#f85149; font-family:monospace; font-weight:bold;'>{tid}</td>
                <td>{clean_cat}</td>
                <td><span class='badge' style='background:{bg_color};'>{clean_status.upper()}</span></td>
                <td style='font-weight:bold; text-align:center;'>{rating_display}</td>
                <td>{data['text']}</td>
            </tr>
        """
        
    html_content += """
        </table>
        <p style='text-align:center; color:#8b949e; margin-top:30px; font-size:12px;'>
            Generated by Claxen Systems Audit Engine
        </p>
    </body>
    </html>
    """
    
    try:
        with open(filename, 'w', encoding='utf-8') as f: 
            f.write(html_content)
        with open(filename, 'rb') as f: 
            bot.send_document(ADMIN_GROUP_ID, f, caption="📊 Professional Audit Dashboard Generated")
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating report: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ==========================================
# ⭐ USER RATING HANDLER
# ==========================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('rate_'))
def handle_rating(call):
    parts = call.data.split('_')
    stars = parts[1]
    tid = parts[2]
    
    if tid in tickets_db:
        tickets_db[tid]['rating'] = int(stars)
        save_tickets()
        
        lang = tickets_db[tid].get('lang', 'en')
        if lang == 'en':
            thank_you_msg = f"Thank you for your feedback! You rated: {'⭐'*int(stars)}"
        else:
            thank_you_msg = f"प्रतिक्रिया के लिए धन्यवाद! आपकी रेटिंग: {'⭐'*int(stars)}"
            
        bot.edit_message_text(thank_you_msg, call.message.chat.id, call.message.message_id)

# ==========================================
# 🛠️ ADMIN ACTION HANDLERS
# ==========================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('st_') or c.data.startswith('admin_ban_'))
def handle_admin_actions(call):
    if 'ban' in call.data:
        target_uid = int(call.data.split('_')[2])
        banned_users.add(target_uid)
        bot.answer_callback_query(call.id, "User has been Banned! 🚫")
        return
        
    parts = call.data.split('_')
    action = parts[1]
    student_id = int(parts[2])
    tid = parts[3]
    
    # 🌟 MAXIMUM DETAILED PROFESSIONAL MESSAGES
    msg_english_rejected = f"❌ <b>TICKET REJECTED ({tid})</b>\n\nUnfortunately, your complaint has been officially rejected by the school administration. Possible reasons include insufficient information provided, or the issue not violating any school policies. If you think this is a mistake, please submit a new detailed report."
    msg_hindi_rejected = f"❌ <b>रिपोर्ट खारिज ({tid})</b>\n\nक्षमा करें, स्कूल प्रशासन ने आपकी शिकायत को आधिकारिक तौर पर खारिज कर दिया है। अधूरी जानकारी या स्कूल के नियमों का उल्लंघन नहीं होना इसका कारण हो सकता है। कृपया नई विस्तृत रिपोर्ट दर्ज करें।"
    
    msg_english_pending = f"⏳ <b>TICKET PENDING ({tid})</b>\n\nYour report has been successfully placed in the pending queue. The administration is reviewing complaints sequentially. Please be patient, we will get to your issue shortly."
    msg_hindi_pending = f"⏳ <b>प्रोग्रेस अपडेट ({tid})</b>\n\nआपकी रिपोर्ट अभी पेंडिंग कतार में सुरक्षित है। हमारी टीम शिकायतों की क्रमबद्ध समीक्षा कर रही है। कृपया धैर्य रखें, हम जल्द ही आपकी समस्या देखेंगे।"
    
    msg_english_working = f"⚙️ <b>INVESTIGATION STARTED ({tid})</b>\n\nExcellent news! The school administration has officially started an investigation based on your report. We are actively working on the ground to fix this issue as soon as possible."
    msg_hindi_working = f"⚙️ <b>कार्यवाही शुरू ({tid})</b>\n\nअच्छी खबर! स्कूल प्रशासन ने आपकी शिकायत पर आधिकारिक रूप से जांच और कार्यवाही शुरू कर दी है। हम इस समस्या को जल्द से जल्द सुलझाने के लिए काम कर रहे हैं।"
    
    msg_english_solved = f"✅ <b>ISSUE RESOLVED ({tid})</b>\n\nThe school administration has successfully investigated and resolved your complaint. Thank you for helping us make our school environment safer and better!\n\n<i>Please rate your overall experience below:</i>"
    msg_hindi_solved = f"✅ <b>समस्या का समाधान! ({tid})</b>\n\nस्कूल प्रशासन ने आपकी शिकायत की सफलतापूर्वक जांच कर उसका समाधान कर लिया है। स्कूल को सुरक्षित और बेहतर बनाने में हमारी मदद करने के लिए धन्यवाद!\n\n<i>कृपया अपने अनुभव की रेटिंग दें:</i>"
    
    status_map = {
        'rej': {'label': '❌ Rejected', 'en': msg_english_rejected, 'hi': msg_hindi_rejected},
        'pen': {'label': '⏳ Pending', 'en': msg_english_pending, 'hi': msg_hindi_pending},
        'wrk': {'label': '⚙️ Working', 'en': msg_english_working, 'hi': msg_hindi_working},
        'sol': {'label': '✅ Solved', 'en': msg_english_solved, 'hi': msg_hindi_solved}
    }
    
    current_status = status_map.get(action)
    
    if tid in tickets_db:
        # Auto-Burn Trigger setup
        if action == 'sol':
            tickets_db[tid]['resolved_at'] = time.time()
            try: 
                burn_msg = f"🚮 <b>Burn Audit Log Activated:</b> Ticket {tid} will be permanently removed from database in 7 days."
                bot.send_message(ADMIN_GROUP_ID, burn_msg, parse_mode="HTML")
            except Exception: 
                pass
        
        tickets_db[tid]['status'] = current_status['label']
        save_tickets()
        
        # Update the Admin's inline message
        old_text = call.message.text
        new_text = html.escape(old_text.split('Status:')[0]) + f"Status: <b>{current_status['label']}</b>"
        bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        
        # Send notification to the Student
        lang = tickets_db[tid].get('lang', 'en')
        student_notification_text = current_status[lang]
        
        # Add Rating Keyboard if Solved
        rating_markup = None
        if action == 'sol':
            rating_markup = InlineKeyboardMarkup(row_width=5)
            rating_markup.add(
                InlineKeyboardButton("1⭐", callback_data=f"rate_1_{tid}"),
                InlineKeyboardButton("2⭐", callback_data=f"rate_2_{tid}"),
                InlineKeyboardButton("3⭐", callback_data=f"rate_3_{tid}"),
                InlineKeyboardButton("4⭐", callback_data=f"rate_4_{tid}"),
                InlineKeyboardButton("5⭐", callback_data=f"rate_5_{tid}")
            )
            
        try: 
            bot.send_message(student_id, student_notification_text, parse_mode="HTML", reply_markup=rating_markup)
        except Exception as e: 
            print(f"Failed to send notification to student: {e}")

# ==========================================
# 🚀 INITIALIZATION
# ==========================================
if __name__ == '__main__':
    # 1. Start the Flask Web Server for Render Port Binding
    web_thread = Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    # 2. Start the Auto-Purge Daemon
    purge_thread = Thread(target=purge_old_tickets_daemon)
    purge_thread.daemon = True
    purge_thread.start()
    
    # 3. Start the Telegram Bot Polling
    print("B3 Safeguarding Bot is Starting...")
    bot.polling(none_stop=True)
        
