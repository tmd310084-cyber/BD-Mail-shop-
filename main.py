import telebot

from telebot import types
import io

# কনফিগারেশন
API_TOKEN = '8558230669:AAE9ABn4jCcffAKxkXgKG_JAfVs3L3Ht4Qg'
ADMIN_ID = 8307689863
LOG_GROUP_ID = -1003537537264
bot = telebot.TeleBot(API_TOKEN)

# ডাটাবেজ (সহজ রাখার জন্য মেমোরিতে রাখা হয়েছে)
users = {} # {id: {'bal': 0, 'ref': 0, 'orders': 0, 'username': ''}}
stock = {
    "Fresh Gmail": {"price": 10, "items": []},
    "FB Mail": {"price": 5, "items": []},
    "Login Hotmail": {"price": 8, "items": []},
    "OTP Hotmail": {"price": 12, "items": []},
    "Login Outlook mail": {"price": 7, "items": []},
    "TOP Outlook mail": {"price": 15, "items": []},
    "Fake Gmail": {"price": 3, "items": []}
}
vpn_stock = {"NORD VPN": 50, "Express VPN": 100}

# --- কিবোর্ড ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("👤 Balance", "💳 Deposit")
    markup.add("📧 Buy Mail", "🛡️ Buy VPN")
    markup.add("👨‍💻 Support Admin", "🔗 Referral")
    if uid == ADMIN_ID:
        markup.add("⚙️ Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username or "No Username"
    
    if uid not in users:
        # রেফারেল চেক
        ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        users[uid] = {'bal': 0, 'ref': 0, 'orders': 0, 'username': uname}
        
        if ref_id and int(ref_id) in users and int(ref_id) != uid:
            users[int(ref_id)]['bal'] += 0.20
            users[int(ref_id)]['ref'] += 1
            bot.send_message(ref_id, "🎊 কেউ আপনার লিঙ্কে জয়েন করেছে! আপনি ০.২০ টাকা পেয়েছেন।")

    bot.send_message(message.chat.id, "👋 স্বাগতম! আপনার প্রয়োজনীয় সার্ভিসটি বেছে নিন।", reply_markup=main_menu(uid))

# 1. Balance Button
@bot.message_handler(func=lambda m: m.text == "👤 Balance")
def balance(message):
    u = users[message.from_user.id]
    text = (f"💰 আপনার ব্যালেন্স: {u['bal']:.2f} টাকা\n"
            f"📦 টোটাল অর্ডার: {u['orders']}টি\n"
            f"👥 টোটাল রেফার: {u['ref']} জন")
    bot.reply_to(message, text)

# 2. Deposit System
@bot.message_handler(func=lambda m: m.text == "💳 Deposit")
def deposit(message):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("bKash", callback_data="dep_bk"),
           types.InlineKeyboardButton("Nagad", callback_data="dep_ng"),
           types.InlineKeyboardButton("Binance", callback_data="dep_bn"))
    bot.send_message(message.chat.id, "পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dep_"))
def process_dep_step1(call):
    method = call.data.split("_")[1]
    bot.send_message(call.message.chat.id, "আপনি কত টাকা ডিপোজিট করতে চান? (শুধুমাত্র সংখ্যা লিখুন)")
    bot.register_next_step_handler(call.message, process_dep_step2, method)

def process_dep_step2(message, method):
    try:
        amount = float(message.text)
        nums = {"bk": "01820916617 (bKash)", "ng": "01704462014 (Nagad)", "bn": "1179810469 (Binance ID)"}
        bot.send_message(message.chat.id, f"আমাদের {nums[method]} নম্বরে {amount} টাকা সেন্ডমানি করে স্ক্রিনশট দিন।")
        bot.register_next_step_handler(message, process_dep_admin, amount, method)
    except:
        bot.send_message(message.chat.id, "❌ ভুল সংখ্যা। আবার চেষ্টা করুন।")

def process_dep_admin(message, amount, method):
    if message.content_type == 'photo':
        uid = message.from_user.id
        uname = message.from_user.username
        
        # অ্যাডমিনকে পাঠানো
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("Accept ✅", callback_data=f"confirm_{uid}_{amount}"),
               types.InlineKeyboardButton("Reject ❌", callback_data=f"reject_{uid}"))
        
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                       caption=f"🔔 নতুন ডিপোজিট!\n👤 ইউজার: @{uname}\n🆔 আইডি: {uid}\n💰 পরিমাণ: {amount}\n💳 মেথড: {method}", 
                       reply_markup=mk)
        bot.send_message(message.chat.id, "⏳ আপনার অনুরোধ পাঠানো হয়েছে। অ্যাডমিন চেক করে ব্যালেন্স অ্যাড করে দিবে।")
    else:
        bot.send_message(message.chat.id, "❌ দয়া করে স্ক্রিনশট (Photo) দিন।")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("confirm_", "reject_")))
def admin_action(call):
    data = call.data.split("_")
    uid = int(data[1])
    
    if data[0] == "confirm":
        amount = float(data[2])
        users[uid]['bal'] += amount
        bot.send_message(uid, f"✅ আপনার {amount} টাকা ডিপোজিট সফল হয়েছে!")
        bot.edit_message_caption("✅ একসেপ্ট করা হয়েছে", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(uid, "❌ আপনার ডিপোজিট অনুরোধ রিজেক্ট করা হয়েছে।")
        bot.edit_message_caption("❌ রিজেক্ট করা হয়েছে", call.message.chat.id, call.message.message_id)

# 3. Buy Mail System
@bot.message_handler(func=lambda m: m.text == "📧 Buy Mail")
def buy_mail(message):
    mk = types.InlineKeyboardMarkup()
    for cat in stock:
        mk.add(types.InlineKeyboardButton(f"{cat} - {stock[cat]['price']} TK (Stock: {len(stock[cat]['items'])})", callback_data=f"mail_{cat}"))
    bot.send_message(message.chat.id, "মেইল ক্যাটাগরি বেছে নিন:", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mail_"))
def mail_order_count(call):
    cat = call.data.replace("mail_", "")
    bot.send_message(call.message.chat.id, f"কয়টি {cat} নিতে চান? সংখ্যা লিখুন।")
    bot.register_next_step_handler(call.message, mail_delivery, cat)

def mail_delivery(message, cat):
    try:
        count = int(message.text)
        uid = message.from_user.id
        price = stock[cat]['price'] * count
        
        if len(stock[cat]['items']) < count:
            bot.send_message(message.chat.id, "❌ পর্যাপ্ত স্টক নেই।")
        elif users[uid]['bal'] < price:
            bot.send_message(message.chat.id, "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়।")
        else:
            # ডেলিভারি
            delivered = stock[cat]['items'][:count]
            stock[cat]['items'] = stock[cat]['items'][count:]
            users[uid]['bal'] -= price
            users[uid]['orders'] += 1
            
            # ফাইল তৈরি
            file_content = ""
            for i, m in enumerate(delivered, 1):
                file_content += f"{i}. {m}\n"
            
            file = io.BytesIO(file_content.encode())
            file.name = f"{cat}_order.txt"
            bot.send_document(message.chat.id, file, caption=f"✅ সফলভাবে {count}টি মেইল ডেলিভারি করা হলো।")
            
            # গ্রুপে লগ পাঠানো
            log_text = (f"🛍️ নতুন অর্ডার!\n👤 ইউজার: @{message.from_user.username}\n💰 ব্যালেন্স: {users[uid]['bal']}\n"
                        f"👥 রেফার: {users[uid]['ref']}\n📦 অর্ডার: {count}x {cat}")
            bot.send_message(LOG_GROUP_ID, log_text)
    except:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট।")

# 5. Support Admin
@bot.message_handler(func=lambda m: m.text == "👨‍💻 Support Admin")
def support(message):
    bot.send_message(message.chat.id, "সরাসরি যোগাযোগ করুন: @TOHID_Admin2")

# 6. Referral
@bot.message_handler(func=lambda m: m.text == "🔗 Referral")
def referral(message):
    uid = message.from_user.id
    ref_link = f"https://t.me/{bot.get_me().username}?start={uid}"
    text = (f"👥 আপনার রেফার: {users[uid]['ref']} জন\n"
            f"💰 প্রতি রেফারে পাবেন: ০.২০ টাকা\n\n"
            f"🔗 আপনার রেফার লিঙ্ক:\n{ref_link}")
    bot.send_message(message.chat.id, text)

# 7. Admin Panel
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("➕ Add Stock", "📈 Edit Price")
    mk.add("📊 Total Users", "📢 Broadcast")
    mk.add("💰 Edit User Bal", "🏠 Back to Main")
    bot.send_message(message.chat.id, "🛠 অ্যাডমিন প্যানেল", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "➕ Add Stock" and m.from_user.id == ADMIN_ID)
def add_stock_step1(message):
    mk = types.InlineKeyboardMarkup()
    for cat in stock:
        mk.add(types.InlineKeyboardButton(cat, callback_data=f"add_{cat}"))
    bot.send_message(message.chat.id, "কোন ক্যাটাগরিতে স্টক অ্যাড করবেন?", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def add_stock_step2(call):
    cat = call.data.replace("add_", "")
    bot.send_message(call.message.chat.id, f"{cat}-এর মেইলগুলো লাইন বাই লাইন লিখুন।")
    bot.register_next_step_handler(call.message, add_stock_final, cat)

def add_stock_final(message, cat):
    new_items = message.text.split('\n')
    stock[cat]['items'].extend(new_items)
    bot.send_message(message.chat.id, f"✅ সফলভাবে {len(new_items)}টি মেইল অ্যাড হয়েছে।")

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast_step1(message):
    bot.send_message(message.chat.id, "সকল ইউজারের জন্য মেসেজটি লিখুন:")
    bot.register_next_step_handler(message, broadcast_final)

def broadcast_final(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 নোটিশ:\n\n{message.text}")
        except: pass
    bot.send_message(message.chat.id, "✅ ব্রডকাস্ট সম্পন্ন।")

@bot.message_handler(func=lambda m: m.text == "🏠 Back to Main")
def back_home(message):
    bot.send_message(message.chat.id, "মেইন মেনু:", reply_markup=main_menu(message.from_user.id))
# --- Edit Price বাটন কার্যকর করার কোড ---
@bot.message_handler(func=lambda m: m.text == "📈 Edit Price" and m.from_user.id == ADMIN_ID)
def edit_price_start(message):
    markup = types.InlineKeyboardMarkup()
    # স্টকে থাকা ক্যাটাগরিগুলো বাটনে দেখাবে
    for category in stock:
        price = stock[category]['price']
        markup.add(types.InlineKeyboardButton(f"{category} ({price} TK)", callback_data=f"setprice_{category}"))
    bot.send_message(message.chat.id, "কোন ক্যাটাগরির দাম পরিবর্তন করতে চান?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setprice_"))
def edit_price_step2(call):
    category = call.data.replace("setprice_", "")
    bot.send_message(call.message.chat.id, f"এখন {category}-এর নতুন দামটি লিখুন (যেমন: ২০):")
    # ইউজারের পরবর্তী মেসেজটি দাম হিসেবে গ্রহণ করবে
    bot.register_next_step_handler(call.message, edit_price_final, category)

def edit_price_final(message, category):
    try:
        new_price = int(message.text)
        stock[category]['price'] = new_price
        bot.send_message(message.chat.id, f"✅ সফল! এখন থেকে {category}-এর নতুন দাম {new_price} টাকা।")
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল হয়েছে! দাম হিসেবে শুধুমাত্র সংখ্যা (যেমন: ১৫) লিখুন।")
# --- ১. Find User Info বাটন (ইউজার আইডি ও ব্যালেন্স দেখা) ---
@bot.message_handler(func=lambda m: m.text == "🔍 Find User ID" and m.from_user.id == ADMIN_ID)
def find_user_start(message):
    bot.send_message(message.chat.id, "ইউজারের ইউজারনেমটি লিখুন (@ ছাড়া):")
    bot.register_next_step_handler(message, find_user_final)

def find_user_final(message):
    target = message.text.strip()
    found = False
    for uid, info in users.items():
        if info.get('username') == target:
            text = (f"✅ তথ্য পাওয়া গেছে!\n\n🆔 আইডি: `{uid}`\n"
                    f"💰 ব্যালেন্স: {info['bal']} TK\n"
                    f"📦 মোট অর্ডার: {info['orders']} টি")
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
            found = True
            break
    if not found:
        bot.send_message(message.chat.id, "❌ এই ইউজারনেমটি ডাটাবেজে নেই।")

# --- ২. মেইন মেনুতে ফেরার বাটন ---
@bot.message_handler(func=lambda m: m.text == "🏠 Back to Main")
def go_home(message):
    bot.send_message(message.chat.id, "🏠 মেইন মেনু:", reply_markup=main_menu(message.from_user.id))

# এটিই হবে ফাইলের একদম শেষ লাইন। #কোনো স্পেস ছাড়া একদম বামে লেগে থাকবে।
bot.infinity_polling()