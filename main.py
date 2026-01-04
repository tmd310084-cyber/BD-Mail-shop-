import telebot
import json
import os
from telebot import types

# --- কনফিগারেশন ---
TOKEN = "8577470136:AAEfMUyad5cFlFJvOOUcoxzwtRdcw5iN_AA"
ADMIN_ID = 8307689863
LOG_GROUP_ID = -1003463559967
DB_FILE = "bot_db.json"

bot = telebot.TeleBot(TOKEN)

# --- ডাটাবেস ফাংশন ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "categories": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# --- মেইন কিবোর্ড ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btns = ["VPN", "Balance", "Deposit", "My Order", "Support Admin"]
    markup.add(*[types.KeyboardButton(b) for b in btns])
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))
    return markup

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "bal": 0.0, 
            "orders": [], 
            "username": message.from_user.username,
            "dep_count": 0,
            "refers": 0
        }
        save_db(db)
    bot.send_message(message.chat.id, "স্বাগতম! নিচের মেনু থেকে অপশন সিলেক্ট করুন।", reply_markup=main_menu(message.from_user.id))

# --- VPN বাটন ---
@bot.message_handler(func=lambda m: m.text == "VPN")
def vpn_list(message):
    markup = types.InlineKeyboardMarkup()
    for cat, data in db["categories"].items():
        markup.add(types.InlineKeyboardButton(f"{cat} - {data['price']} TK", callback_data=f"buy_{cat}"))
    bot.send_message(message.chat.id, "আমাদের উপলব্ধ VPN ক্যাটাগরি সমূহ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_vpn(call):
    cat = call.data.split("_")[1]
    price = db["categories"][cat]["price"]
    user_bal = db["users"][str(call.from_user.id)]["bal"]
    
    text = f"🛡 VPN-এর নাম: {cat}\n💰 রেট: {price} TK\n💵 আপনার ব্যালেন্স: {user_bal} TK"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Confirm", callback_data=f"conf_order_{cat}"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_order_"))
def process_order(call):
    cat = call.data.split("_")[2]
    uid = str(call.from_user.id)
    price = db["categories"][cat]["price"]
    
    if db["users"][uid]["bal"] < price:
        bot.send_message(call.message.chat.id, "❌ পর্যাপ্ত ব্যালেন্স নেই! দয়া করে ডিপোজিট করুন।")
    else:
        # এডমিনকে জানানো
        admin_text = (f"🆕 নতুন অর্ডার!\n🆔 আইডি: {uid}\n👤 ইউজার: @{call.from_user.username}\n"
                      f"📦 VPN: {cat}\n💸 দাম: {price} TK\n💵 ব্যালেন্স: {db['users'][uid]['bal']} TK")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Confirm Order", callback_data=f"adm_conf_{uid}_{cat}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
        bot.send_message(call.message.chat.id, "✅ আপনার অর্ডারটি এডমিনের কাছে পাঠানো হয়েছে।")

# --- ডিপোজিট সিস্টেম ---
@bot.message_handler(func=lambda m: m.text == "Deposit")
def deposit(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Bkash", "Nagad", "Binance", "🏠 Back Main")
    bot.send_message(message.chat.id, "পেমেন্ট মাধ্যম সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Bkash", "Nagad", "Binance"])
def dep_step1(message):
    method = message.text
    msg = bot.send_message(message.chat.id, f"{method}-এ কত টাকা ডিপোজিট করতে চান? সংখ্যায় লিখুন:")
    bot.register_next_step_handler(msg, dep_step2, method)

def dep_step2(message, method):
    try:
        amount = float(message.text)
        num = "01820916617" if method == "Bkash" else "01704462014" if method == "Nagad" else "ID: 1179810469"
        text = f"আমাদের {method} নাম্বার: {num}\nপরিমাণ: {amount} TK\nটাকা পাঠিয়ে স্ক্রিনশট দিন।"
        msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(msg, dep_step3, method, amount)
    except:
        bot.send_message(message.chat.id, "ভুল ইনপুট! আবার চেষ্টা করুন।")

def dep_step3(message, method, amount):
    if message.content_type == 'photo':
        uid = str(message.from_user.id)
        bot.send_message(message.chat.id, "✅ স্ক্রিনশট গ্রহণ করা হয়েছে। এডমিন চেক করে ব্যালেন্স এড করে দিবে।")
        
        # এডমিন অপশন
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Accept", callback_data=f"dep_acc_{uid}_{amount}"),
                   types.InlineKeyboardButton("Reject", callback_data=f"dep_rej_{uid}"))
        
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                       caption=f"💰 নতুন ডিপোজিট!\n👤 ইউজার: @{message.from_user.username}\n💵 পরিমাণ: {amount} TK\n🆔 আইডি: {uid}\n🛠 মাধ্যম: {method}", 
                       reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "দয়া করে স্ক্রিনশট (Photo) পাঠান।")

# --- ডিপোজিট হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("dep_"))
def handle_deposit(call):
    data = call.data.split("_")
    uid = data[2]
    if data[1] == "acc":
        amount = float(data[3])
        db["users"][uid]["bal"] += amount
        db["users"][uid]["dep_count"] += 1
        save_db(db)
        bot.send_message(uid, f"✅ আপনার {amount} TK ডিপোজিট সফল হয়েছে!")
        bot.edit_message_caption("✅ ডিপোজিট এপ্রুভ করা হয়েছে।", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(uid, "❌ আপনার ডিপোজিটটি রিজেক্ট করা হয়েছে।")
        bot.edit_message_caption("❌ ডিপোজিট রিজেক্ট করা হয়েছে।", call.message.chat.id, call.message.message_id)

# --- এডমিন প্যানেল এবং অন্যান্য বাটন (সংক্ষিপ্ত) ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Change Rate", "📊 Stats", "📢 Broadcast", "💰 Edit Bal", "➕ Category", "🆔 Get User ID", "🏠 Back Main")
    bot.send_message(message.chat.id, "🛠 এডমিন প্যানেল", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Balance")
def show_balance(message):
    u = db["users"].get(str(message.from_user.id))
    bot.send_message(message.chat.id, f"💵 আপনার ব্যালেন্স: {u['bal']} TK\n📦 মোট অর্ডার: {len(u['orders'])}")

@bot.message_handler(func=lambda m: m.text == "Support Admin")
def support(message):
    bot.send_message(message.chat.id, "অ্যাডমিন সাপোর্ট: https://t.me/xt_tohid_4253")

@bot.message_handler(func=lambda m: m.text == "🏠 Back Main")
def back(message):
    bot.send_message(message.chat.id, "মূল মেনু:", reply_markup=main_menu(message.from_user.id))

# --- ক্যাটাগরি ম্যানেজমেন্ট ---
@bot.message_handler(func=lambda m: m.text == "➕ Category" and m.from_user.id == ADMIN_ID)
def admin_cat(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Add Category", "Delete Category", "🏠 Back Main")
    bot.send_message(message.chat.id, "ক্যাটাগরি ম্যানেজমেন্ট:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Add Category" and m.from_user.id == ADMIN_ID)
def add_cat_start(message):
    msg = bot.send_message(message.chat.id, "ক্যাটাগরির নাম লিখুন:")
    bot.register_next_step_handler(msg, add_cat_save)

def add_cat_save(message):
    name = message.text
    db["categories"][name] = {"price": 0}
    save_db(db)
    bot.send_message(message.chat.id, f"✅ {name} ক্যাটাগরি অ্যাড হয়েছে। রেট সেট করতে Change Rate ব্যবহার করুন।")

# বটের রান শুরু
bot.polling(none_stop=True)
