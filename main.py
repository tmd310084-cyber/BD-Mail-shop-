import telebot
from telebot import types
import json
import os

# --- কনফিগারেশন ---
API_TOKEN = '8558230669:AAE-uoWZHkNAZdD1ogDd6LBY3SX6_8AFMfU'
ADMIN_ID = 8307689863
LOG_GROUP_ID = -1003537537264
CHANNEL_ID = "@xt_tohid_4253" # চ্যানেলের ইউজারনেম
CHANNEL_LINK = "https://t.me/xt_tohid_4253"

bot = telebot.TeleBot(API_TOKEN)
DATA_FILE = "bot_database.json"

# --- ডাটাবেস ফাংশন ---
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                if "users" not in d: d["users"] = {}
                if "categories" not in d: d["categories"] = {}
                return d
        except: pass
    return {"users": {}, "categories": {}}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# --- মিডলওয়্যার ---
def is_joined(uid):
    try:
        status = bot.get_chat_member(CHANNEL_ID, uid).status
        return status in ['member', 'administrator', 'creator']
    except: return True # চ্যানেলে বট এডমিন না থাকলে এটি ট্রু রিটার্ন করবে

def main_kb(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💰 Balance", "💳 Deposit")
    markup.add("📧 Buy Mail", "👨‍💻 Support Admin")
    markup.add("🔗 Rafael", "❓ Help AI")
    if uid == ADMIN_ID: markup.add("⚙️ Admin Panel")
    return markup

# --- ১. স্টার্ট ফিচার (জয়েন চেক ও রেফার) ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        db["users"][uid] = {'bal': 0, 'orders': 0, 'refers': 0, 'dep_count': 0, 'username': message.from_user.username}
        if ref_id and ref_id in db["users"] and ref_id != uid:
            db["users"][ref_id]['bal'] += 1
            db["users"][ref_id]['refers'] += 1
            try: bot.send_message(ref_id, "🎁 অভিনন্দন! আপনার রেফার লিংকে একজন জয়েন করায় ১ টাকা বোনাস পেয়েছেন।")
            except: pass
        save_db(db)

    if not is_joined(message.from_user.id):
        mk = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Join Channel", url=CHANNEL_LINK))
        return bot.send_message(message.chat.id, "❌ আপনি আমাদের চ্যানেলে জয়েন করেননি! জয়েন করে আবার /start দিন।", reply_markup=mk)

    bot.send_message(message.chat.id, "👋 স্বাগতম BD Male Shop-এ!", reply_markup=main_kb(message.from_user.id))

# --- ২. ইউজার মেনু বাটন লজিক ---

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    u = db["users"].get(str(message.from_user.id))
    bot.send_message(message.chat.id, f"👤 ইউজার: @{u['username']}\n💵 বর্তমান ব্যালেন্স: {u['bal']} TK\n📦 মোট অর্ডার: {u['orders']}\n👥 মোট রেফার: {u['refers']}")

@bot.message_handler(func=lambda m: m.text == "💳 Deposit")
def deposit(message):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Bkash", callback_data="dep_bkash"),
           types.InlineKeyboardButton("Nagad", callback_data="dep_nagad"),
           types.InlineKeyboardButton("Binance", callback_data="dep_binance"))
    bot.send_message(message.chat.id, "নিচের কোন মাধ্যমে ডিপোজিট করতে চান?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dep_"))
def dep_step1(c):
    method = c.data.split('_')[1]
    msg = bot.send_message(c.message.chat.id, f"আপনি কত টাকা {method}-এ ডিপোজিট করতে চান? (শুধু সংখ্যা লিখুন):")
    bot.register_next_step_handler(msg, lambda m: dep_step2(m, method))

def dep_step2(message, method):
    amount = message.text
    num = "01820916617" if method == "bkash" else "01704462014" if method == "nagad" else "ID: 1179810469"
    msg = bot.send_message(message.chat.id, f"💳 মেথড: {method}\n💰 পরিমাণ: {amount} TK\n📍 নাম্বার/আইডি: `{num}`\n\nটাকা পাঠানোর পর পেমেন্টের একটি স্ক্রিনশট এখানে দিন:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: dep_step_admin(m, method, amount))

def dep_step_admin(message, method, amount):
    if message.content_type != 'photo':
        return bot.send_message(message.chat.id, "❌ ভুল ইনপুট! আবার ডিপোজিট বাটনে ক্লিক করে স্ক্রিনশট ফটো হিসেবে পাঠান।")

    mk = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ Accept", callback_data=f"adm_acc_{message.from_user.id}_{amount}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
                   caption=f"🔔 নতুন ডিপোজিট রিকোয়েস্ট!\n👤 ইউজার: @{message.from_user.username}\n🆔 আইডি: {message.from_user.id}\n💵 পরিমাণ: {amount} TK\n💳 মেথড: {method}",
                   reply_markup=mk)
    bot.send_message(message.chat.id, "⏳ আপনার রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুগ্রহ করে অপেক্ষা করুন।")

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def admin_action(c):
    data = c.data.split('_')
    action, uid, amt = data[1], data[2], data[3] if len(data)>3 else 0
    if action == "acc":
        db["users"][uid]['bal'] += float(amt)
        db["users"][uid]['dep_count'] += 1
        save_db(db)
        bot.send_message(uid, f"✅ আপনার {amt} টাকা ডিপোজিট রিকোয়েস্ট একসেপ্ট করা হয়েছে।")
        bot.answer_callback_query(c.id, "Accepted")
    else:
        bot.send_message(uid, "❌ আপনার ডিপোজিট রিকোয়েস্ট রিজেক্ট করা হয়েছে।")
        bot.answer_callback_query(c.id, "Rejected")
    bot.delete_message(c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "📧 Buy Mail")
def buy_mail(message):
    if not db["categories"]:
        return bot.send_message(message.chat.id, "❌ বর্তমানে কোনো ক্যাটাগরি নেই।")
    mk = types.InlineKeyboardMarkup()
    for cat in db["categories"]:
        mk.add(types.InlineKeyboardButton(f"{cat} - {db['categories'][cat]['price']} TK", callback_data=f"buy_{cat}"))
    bot.send_message(message.chat.id, "🛒 ক্যাটাগরি বেছে নিন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_step1(c):
    cat = c.data.split('_', 1)[1]
    u = db["users"][str(c.from_user.id)]
    info = db["categories"][cat]
    bot.send_message(c.message.chat.id, f"📦 ক্যাটাগরি: {cat}\n💰 দাম: {info['price']} TK\n💵 আপনার ব্যালেন্স: {u['bal']} TK\n📉 স্টক: {len(info['stock'])}\n\nকয়টি মেইল কিনতে চান? সংখ্যা লিখুন:")
    bot.register_next_step_handler(c.message, lambda m: buy_step2(m, cat))

def buy_step2(message, cat):
    try:
        qty = int(message.text)
        uid = str(message.from_user.id)
        u = db["users"][uid]
        info = db["categories"][cat]

        if qty <= 0: return bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন।")
        if len(info['stock']) < qty: return bot.send_message(message.chat.id, "❌ দুঃখিত! পর্যাপ্ত স্টক নেই।")

        total_cost = qty * info['price']
        if u['bal'] < total_cost: return bot.send_message(message.chat.id, "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই।")

        # ডেলিভারি প্রসেস
        bought_mails = info['stock'][:qty]
        db["categories"][cat]['stock'] = info['stock'][qty:]
        db["users"][uid]['bal'] -= total_cost
        db["users"][uid]['orders'] += 1
        save_db(db)

        mail_text = "\n".join([f"{i+1} নম্বর মেইল: {m}" for i, m in enumerate(bought_mails)])
        with open("delivery.txt", "w") as f: f.write(mail_text)

        bot.send_document(message.chat.id, open("delivery.txt", "rb"), caption=f"✅ সফল ডেলিভারি!\n📦 ক্যাটাগরি: {cat}\n💰 খরচ: {total_cost} TK")

        # ৪. অর্ডার লগ গ্রুপ [cite: -1003537537264]
        bot.send_message(LOG_GROUP_ID, f"🛒 নতুন অর্ডার!\n👤 ইউজার: @{u['username']}\n💰 ব্যালেন্স: {u['bal']} TK\n👥 রেফার: {u['refers']}\n📧 পণ্য: {cat}\n📦 পরিমাণ: {qty}")
    except:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন।")

@bot.message_handler(func=lambda m: m.text == "👨‍💻 Support Admin")
def support(message):
    bot.send_message(message.chat.id, "👨‍💻 আমাদের অ্যাডমিন আইডি: @TOHID_Admin2")

@bot.message_handler(func=lambda m: m.text == "🔗 Rafael")
def rafael(message):
    u = db["users"][str(message.from_user.id)]
    bot.send_message(message.chat.id, f"👥 আপনার মোট রেফার: {u['refers']}\n🎁 প্রতি রেফারে পাবেন: ১ টাকা\n\n🔗 আপনার রেফার লিংক:\nhttps://t.me/{(bot.get_me()).username}?start={message.from_user.id}")

@bot.message_handler(func=lambda m: m.text == "❓ Help AI")
def help_ai(message):
    msg = bot.send_message(message.chat.id, "🤖 আমি আপনার AI সহযোগী। আপনার যেকোনো প্রশ্ন এখানে লিখুন:")
    bot.register_next_step_handler(msg, ai_logic)

def ai_logic(message):
    text = message.text.lower()
    if "hotmail" in text or "outlook" in text or "code" in text:
        bot.send_message(message.chat.id, "📫 মেইল বক্স চেক করার লিংক: https://dongvanfb.net/read_mail_box")
    elif "ফেসবুক" in text or "facebook" in text:
        bot.send_message(message.chat.id, "💡 ১টি জিমেইল দিয়ে সর্বোচ্চ ৪টি ফেসবুক আইডি খোলা যায়।")
    elif "deposit" in text or "ডিপোজিট" in text:
        bot.send_message(message.chat.id, "💳 ডিপোজিট করতে মেনু থেকে 'Deposit' বাটনে ক্লিক করুন এবং মেথড সিলেক্ট করে স্ক্রিনশট দিন।")
    elif "buy" in text or "কিনব" in text:
        bot.send_message(message.chat.id, "📧 মেইল কিনতে 'Buy Mail' বাটনে ক্লিক করুন এবং আপনার পছন্দের ক্যাটাগরি বেছে নিন।")
    elif "video" in text or "ভিডিও" in text:
        bot.send_message(message.chat.id, f"📺 টিউটোরিয়াল ভিডিও দেখতে আমাদের চ্যানেলে জয়েন করুন: {CHANNEL_LINK}")
    else:
        bot.send_message(message.chat.id, "🤖 আমি আপনার প্রশ্নটি বুঝতে পারিনি। বিস্তারিত জানতে অ্যাডমিনকে নক দিন।")

# --- ৩. অ্যাডমিন প্যানেল লজিক ---

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("📥 Add Stock", "📈 Change Rate", "📊 Stats", "📢 Broadcast", "💰 Edit Bal", "➕ Category", "🆔 Get User ID", "🏠 Back Main")
    bot.send_message(message.chat.id, "🛠 অ্যাডমিন প্যানেলে স্বাগতম:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "📥 Add Stock" and m.from_user.id == ADMIN_ID)
def add_stock_cat(message):
    mk = types.InlineKeyboardMarkup()
    for cat in db["categories"]: mk.add(types.InlineKeyboardButton(cat, callback_data=f"astk_{cat}"))
    bot.send_message(message.chat.id, "কোন ক্যাটাগরিতে স্টক যোগ করবেন?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("astk_"))
def add_stock_input(c):
    cat = c.data.split('_', 1)[1]
    msg = bot.send_message(c.message.chat.id, f"📧 {cat}-এর মেইলগুলো লাইন বাই লাইন লিখুন:")
    bot.register_next_step_handler(msg, lambda m: save_stock(m, cat))

def save_stock(message, cat):
    new_mails = [l.strip() for l in message.text.split('\n') if l.strip()]
    db["categories"][cat]["stock"].extend(new_mails)
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ {len(new_mails)}টি মেইল {cat}-এ যুক্ত হয়েছে।")

@bot.message_handler(func=lambda m: m.text == "📈 Change Rate" and m.from_user.id == ADMIN_ID)
def rate_cat(message):
    mk = types.InlineKeyboardMarkup()
    for cat in db["categories"]: mk.add(types.InlineKeyboardButton(cat, callback_data=f"rate_{cat}"))
    bot.send_message(message.chat.id, "কোনটির দাম পরিবর্তন করবেন?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rate_"))
def rate_input(c):
    cat = c.data.split('_', 1)[1]
    msg = bot.send_message(c.message.chat.id, f"💰 {cat}-এর নতুন দাম লিখুন:")
    bot.register_next_step_handler(msg, lambda m: save_rate(m, cat))

def save_rate(message, cat):
    db["categories"][cat]["price"] = int(message.text)
    save_db(db)
    bot.send_message(ADMIN_ID, "✅ দাম আপডেট হয়েছে।")

@bot.message_handler(func=lambda m: m.text == "📊 Stats" and m.from_user.id == ADMIN_ID)
def stats(message):
    total_u = len(db["users"])
    total_b = sum(u['bal'] for u in db["users"].values())
    bot.send_message(ADMIN_ID, f"📊 পরিসংখ্যান:\n👥 মোট ইউজার: {total_u}\n💰 মোট ব্যালেন্স: {total_b} TK")

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast(message):
    msg = bot.send_message(message.chat.id, "📢 আপনার মেসেজটি লিখুন:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    for uid in db["users"]:
        try: bot.send_message(uid, message.text)
        except: pass
    bot.send_message(ADMIN_ID, "✅ ব্রডকাস্ট সম্পন্ন।")

@bot.message_handler(func=lambda m: m.text == "💰 Edit Bal" and m.from_user.id == ADMIN_ID)
def edit_bal_menu(message):
    mk = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Add Balance", callback_data="eb_add"),
        types.InlineKeyboardButton("Cut Balance", callback_data="eb_cut")
    )
    bot.send_message(message.chat.id, "কি করতে চান?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("eb_"))
def eb_step1(c):
    act = c.data.split('_')[1]
    msg = bot.send_message(c.message.chat.id, "🆔 ইউজারের আইডি দিন:")
    bot.register_next_step_handler(msg, lambda m: eb_step2(m, act))

def eb_step2(message, act):
    uid = message.text
    msg = bot.send_message(ADMIN_ID, "💵 টাকার পরিমাণ দিন:")
    bot.register_next_step_handler(msg, lambda m: eb_final(m, uid, act))

def eb_final(message, uid, act):
    try:
        amt = float(message.text)
        if uid in db["users"]:
            if act == "add": db["users"][uid]['bal'] += amt
            else: db["users"][uid]['bal'] -= amt
            save_db(db)
            bot.send_message(ADMIN_ID, "✅ ব্যালেন্স আপডেট হয়েছে।")
            bot.send_message(uid, f"🔔 আপনার ব্যালেন্স আপডেট করা হয়েছে। বর্তমান ব্যালেন্স: {db['users'][uid]['bal']} TK")
        else: bot.send_message(ADMIN_ID, "❌ আইডি পাওয়া যায়নি।")
    except: bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট।")

@bot.message_handler(func=lambda m: m.text == "➕ Category" and m.from_user.id == ADMIN_ID)
def cat_manage(message):
    mk = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Add Category", callback_data="c_add"),
        types.InlineKeyboardButton("Delete Category", callback_data="c_del")
    )
    bot.send_message(message.chat.id, "ক্যাটাগরি ম্যানেজমেন্ট:", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("c_"))
def cat_action(c):
    act = c.data.split('_')[1]
    if act == "add":
        msg = bot.send_message(c.message.chat.id, "🆕 নতুন ক্যাটাগরির নাম দিন:")
        bot.register_next_step_handler(msg, lambda m: (db["categories"].update({m.text: {"price": 0, "stock": []}}), save_db(db), bot.send_message(ADMIN_ID, "✅ ক্যাটাগরি তৈরি!")))
    else:
        mk = types.InlineKeyboardMarkup()
        for cat in db["categories"]: mk.add(types.InlineKeyboardButton(cat, callback_data=f"cdel_{cat}"))
        bot.send_message(c.message.chat.id, "🗑 ডিলিট করতে ক্লিক করুন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cdel_"))
def cat_delete(c):
    cat = c.data.split('_')[1]
    del db["categories"][cat]
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ {cat} ডিলিট করা হয়েছে।")
    bot.delete_message(c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "🆔 Get User ID" and m.from_user.id == ADMIN_ID)
def get_uid_start(message):
    msg = bot.send_message(message.chat.id, "🔍 ইউজারের ইউজারনেম দিন (যেমন: TOHID_Admin2):")
    bot.register_next_step_handler(msg, get_uid_logic)

def get_uid_logic(message):
    un = message.text.replace('@', '')
    found = False
    for uid, data in db["users"].items():
        if data.get('username') == un:
            bot.send_message(ADMIN_ID, f"🆔 ইউজার আইডি: `{uid}`\n👤 ইউজারনেম: @{un}\n💵 ব্যালেন্স: {data['bal']} TK\n📦 অর্ডার: {data['orders']}\n💳 ডিপোজিট: {data['dep_count']} বার", parse_mode="Markdown")
            found = True; break
    if not found: bot.send_message(ADMIN_ID, "❌ ইউজার খুঁজে পাওয়া যায়নি।")

@bot.message_handler(func=lambda m: m.text == "🏠 Back Main")
def back_main(message):
    bot.send_message(message.chat.id, "🏠 মূল মেনু:", reply_markup=main_kb(message.from_user.id))

# --- রান বোট ---
bot.infinity_polling()