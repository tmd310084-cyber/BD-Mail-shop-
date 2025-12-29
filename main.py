import telebot
from telebot import types
import io
import json
import os

# --- কনফিগারেশন ---
API_TOKEN = '8558230669:AAE-uoWZHkNAZdD1ogDd6LBY3SX6_8AFMfU'
ADMIN_ID = 8307689863
LOG_GROUP_ID = -1003537537264
CHANNEL_LINK = "https://t.me/xt_tohid_4253"
CHANNEL_USERNAME = "@xt_tohid_4253" # '@' সহ চ্যানেলের ইউজারনেম দিন
bot = telebot.TeleBot(API_TOKEN)

# --- ডাটাবেজ ম্যানেজমেন্ট ---
DB_FILE = "database.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "mail_stock": {}, "vpn_stock": {"NORD VPN": 50, "Express VPN": 100}}

def save_db():
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

db = load_db()

# --- জয়েন চেক ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- মেনু ফাংশন ---
def main_menu(uid):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("💰 Balance", "💳 Deposit")
    mk.row("📧 Buy Mail", "🛡️ Buy VPN")
    mk.row("👨‍💻 Support Admin", "👥 Rafael")
    mk.row("❓ Help AI")
    if uid == ADMIN_ID: mk.add("⚙️ Admin Panel")
    return mk

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.username or "No_Username"
    
    if uid not in db["users"]:
        ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        db["users"][uid] = {'bal': 0, 'orders': 0, 'refs': 0, 'uname': uname, 'dep_count': 0, 'ref_by': ref_id}
        if ref_id and ref_id in db["users"] and ref_id != uid:
            db["users"][ref_id]['bal'] += 0.20
            db["users"][ref_id]['refs'] += 1
            bot.send_message(ref_id, "🎁 রেফার বোনাস! আপনার লিংকে একজন জয়েন করায় ০.২০ টাকা পেয়েছেন।")
        save_db()

    if not is_joined(message.from_user.id):
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        mk.add(types.InlineKeyboardButton("✅ Joined", callback_data="check_join"))
        return bot.send_message(message.chat.id, "⚠️ বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=mk)
    
    bot.send_message(message.chat.id, "👋 স্বাগতম! আপনি এখন বটটি ব্যবহার করতে পারেন।", reply_markup=main_menu(int(uid)))

# --- ব্যালেন্স ---
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    u = db["users"][str(message.from_user.id)]
    bot.send_message(message.chat.id, f"👤 ইউজার: @{u['uname']}\n💵 ব্যালেন্স: {u['bal']:.2f} TK\n📦 মোট অর্ডার: {u['orders']}\n👥 মোট রেফার: {u['refs']}")

# --- ডিপোজিট (বিকাশ, নগদ, বাইনান্স) ---
@bot.message_handler(func=lambda m: m.text == "💳 Deposit")
def deposit(message):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("bKash", callback_data="d_bkash"), 
           types.InlineKeyboardButton("Nagad", callback_data="d_nagad"))
    mk.add(types.InlineKeyboardButton("Binance", callback_data="d_binance"))
    bot.send_message(message.chat.id, "টাকা জমা দেওয়ার মাধ্যম বেছে নিন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("d_"))
def dep_step1(call):
    method = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, f"কত টাকা {method} করতে চান? সংখ্যায় লিখুন:")
    bot.register_next_step_handler(msg, lambda m: dep_step2(m, method))

def dep_step2(message, method):
    try:
        amount = float(message.text)
        nums = {"bkash": "01820916617", "nagad": "01704462014", "binance": "ID: 1179810469"}
        msg = bot.send_message(message.chat.id, f"✅ {method} তথ্য: {nums[method]}\nটাকা পাঠিয়ে ট্রানজেকশন স্ক্রিনশট দিন।")
        bot.register_next_step_handler(msg, lambda m: dep_final(m, amount, method))
    except: bot.send_message(message.chat.id, "❌ ভুল ইনপুট।")

def dep_final(message, amount, method):
    if message.content_type != 'photo': return bot.send_message(message.chat.id, "❌ স্ক্রিনশট দিতে হবে।")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ Accept", callback_data=f"p_acc_{message.from_user.id}_{amount}"),
           types.InlineKeyboardButton("❌ Reject", callback_data=f"p_rej_{message.from_user.id}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                   caption=f"🔔 নতুন ডিপোজিট!\n👤 @{message.from_user.username}\n🆔 `{message.from_user.id}`\n💰 {amount} TK\n💳 {method}", reply_markup=mk)
    bot.send_message(message.chat.id, "⌛ রিকোয়েস্ট পাঠানো হয়েছে। অপেক্ষা করুন।")

# --- মেইল ও ভিপিএন বাই লজিক (সংক্ষিপ্ত) ---
@bot.message_handler(func=lambda m: m.text == "📧 Buy Mail")
def buy_mail(message):
    mk = types.InlineKeyboardMarkup()
    for cat in db["mail_stock"]: mk.add(types.InlineKeyboardButton(cat, callback_data=f"bm_{cat}"))
    bot.send_message(message.chat.id, "মেইল ক্যাটাগরি:", reply_markup=mk)

# --- Help AI (আপনার চাওয়া স্পেশাল লজিক) ---
@bot.message_handler(func=lambda m: m.text == "❓ Help AI")
def help_ai(message):
    msg = bot.send_message(message.chat.id, "🤖 আমি আপনার AI সাহায্যকারী। কি জানতে চান লিখুন:")
    bot.register_next_step_handler(msg, ai_logic)

def ai_logic(message):
    query = message.text.lower()
    uid = str(message.from_user.id)
    
    if "ডিপোজিট" in query:
        res = "💳 ডিপোজিট করতে 'Deposit' বাটনে যান, মাধ্যম সিলেক্ট করে টাকা পাঠিয়ে স্ক্রিনশট দিন।"
    elif "মেইল" in query and "কিনবো" in query:
        res = "📧 'Buy Mail' বাটনে গিয়ে ক্যাটাগরি এবং সংখ্যা দিলে ব্যালেন্স থাকলে সাথে সাথে ফাইল পাবেন।"
    elif "ভিপিএন" in query:
        res = f"🛡️ ভিপিএন কিনতে 'Buy VPN' বাটনে গিয়ে অর্ডার করুন। ভিডিও টিউটোরিয়াল: {CHANNEL_LINK}"
    elif "ওটিপি" in query or "লিংক" in query:
        res = "📧 ওটিপি রিড করার লিংক: https://dongvanfb.net/read_mail_box"
    elif "ফেসবুক আইডি" in query or "খোলা যায়" in query:
        res = "✅ একটি ফ্রেশ মেইল দিয়ে ৪টি ফেসবুক আইডি খোলা যায়।"
    elif "তৈরি করছে" in query or "owner" in query:
        res = "👤 এই বটটি তৈরি করেছেন: @TOHID_Admin2"
    else:
        res = "😅 আমি আপনার প্রশ্নটি বুঝতে পারিনি। ডিপোজিট বা মেইল কেনা নিয়ে প্রশ্ন করুন।"
    bot.send_message(message.chat.id, res)

# --- অ্যাডমিন প্যানেল ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_p(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("➕ Add Stock", "📈 Edit Rate")
    mk.row("📊 Total Users", "📢 Broadcast")
    mk.row("💰 Edit Bal", "🔍 Find User ID")
    mk.row("➕ Add Category", "🗑️ Delete Category")
    mk.add("🏠 Back to Main")
    bot.send_message(message.chat.id, "🛠️ অ্যাডমিন প্যানেল", reply_markup=mk)

# --- ১০. Find User ID লজিক ---
@bot.message_handler(func=lambda m: m.text == "🔍 Find User ID")
def find_id(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "🔍 ইউজারের ইউজারনেম দিন (@ ছাড়া):")
    bot.register_next_step_handler(msg, find_id_process)

def find_id_process(message):
    target = message.text
    for uid, data in db["users"].items():
        if data["uname"] == target:
            bot.send_message(message.chat.id, f"✅ ইউজার তথ্য:\n🆔 ID: `{uid}`\n💰 ব্যালেন্স: {data['bal']}\n📦 অর্ডার: {data['orders']}\n💳 ডিপোজিট: {data['dep_count']} বার", parse_mode="Markdown")
            return
    bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি।")

# --- ডিপোজিট একসেপ্ট/রিজেক্ট কলব্যাক ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("p_acc_", "p_rej_")))
def handle_pay(call):
    data = call.data.split("_")
    uid = data[2]
    if data[1] == "acc":
        amount = float(data[3])
        db["users"][uid]["bal"] += amount
        db["users"][uid]["dep_count"] += 1
        save_db()
        bot.send_message(uid, f"✅ অভিনন্দন! আপনার {amount} TK ডিপোজিট সফল হয়েছে।")
        bot.edit_message_caption("✅ Accepted", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(uid, "❌ আপনার ডিপোজিট রিকোয়েস্ট রিজেক্ট করা হয়েছে।")
        bot.edit_message_caption("❌ Rejected", call.message.chat.id, call.message.message_id)

# বটের পোলিং
bot.infinity_polling()