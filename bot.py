import time
import requests
import telebot
from telebot import types

# ==========================================
# 1. ព័ត៌មានកំណត់ប្រព័ន្ធ (CONFIGURATIONS)
# ==========================================

BOT_TOKEN = "8817836194:AAG06X97nyV0Cww1PcU2AB5OZnq_nY8ODB0"
ADMIN_ID = -1004371522384
ADMIN_GROUP_ID = -1004371522384

# API KEYS
SUPPLIER_API_KEY = "kt_c62fdac88096d2dd00d140ea85741e5156094a36"
PAYMENT_API_KEY = "sk_live_mJH7EGC07bzGjhb1kRxx3A4EGkjdlJWE"

# API ENDPOINTS
BAKONG_CHECK_URL = "https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5"
SUPPLIER_TOPUP_URL = "https://api.supplier.com/v1/order"

bot = telebot.TeleBot(BOT_TOKEN)

# ស្ថានភាពប្រព័ន្ធ (System State)
system_status = {"maintenance": False}
user_states = {}

# តម្លៃចំណេញ Default (កំណត់ចាប់ពី $0.01 ឡើងទៅ - បច្ចុប្បន្ន $0.01)
profit_margin = 0.01

# តារាងតម្លៃដើម (Base Cost From Website)
BASE_PACKS = {
    "pack_25": {"name": "25 Diamonds", "base_price": 0.24, "product_id": "ff_25"},
    "pack_100": {"name": "100 Diamonds", "base_price": 0.90, "product_id": "ff_100"},
    "pack_310": {"name": "310 Diamonds", "base_price": 2.74, "product_id": "ff_310"},
    "pack_520": {"name": "520 Diamonds", "base_price": 4.58, "product_id": "ff_520"},
    "pack_1060": {"name": "1060 Diamonds", "base_price": 9.02, "product_id": "ff_1060"},
    "pack_2180": {"name": "2180 Diamonds", "base_price": 18.22, "product_id": "ff_2180"},
    "pack_5600": {"name": "5600 Diamonds", "base_price": 45.08, "product_id": "ff_5600"},
    "pack_11500": {"name": "11500 Diamonds", "base_price": 92.86, "product_id": "ff_11500"},
    "pack_weekly_lite": {"name": "Weekly Lite", "base_price": 0.33, "product_id": "ff_weekly_lite"},
    "pack_weekly_x1": {"name": "Weekly Pass (x1)", "base_price": 1.57, "product_id": "ff_weekly_1"},
    "pack_weekly_x2": {"name": "Weekly Pass (x2)", "base_price": 3.12, "product_id": "ff_weekly_2"},
    "pack_weekly_x3": {"name": "Weekly Pass (x3)", "base_price": 4.67, "product_id": "ff_weekly_3"},
    "pack_monthly_x1": {"name": "Monthly Pass (x1)", "base_price": 7.73, "product_id": "ff_monthly_1"},
    "pack_monthly_x2": {"name": "Monthly Pass (x2)", "base_price": 15.42, "product_id": "ff_monthly_2"},
    "pack_monthly_x3": {"name": "Monthly Pass (x3)", "base_price": 23.12, "product_id": "ff_monthly_3"},
}

def get_selling_price(base_price):
    return round(base_price + profit_margin, 2)

# ==========================================
# 2. HELPER FUNCTIONS (API CALLS)
# ==========================================

def check_khqr_payment(md5_hash):
    headers = {
        "Authorization": f"Bearer {PAYMENT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"md5": md5_hash}
    try:
        response = requests.post(BAKONG_CHECK_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("responseCode") == 0 and data.get("data"):
                return True, data["data"]
    except Exception as e:
        print("KHQR Payment Error:", e)
    return False, None

def send_supplier_topup(user_id, zone_id, product_id):
    headers = {
        "Authorization": f"Bearer {SUPPLIER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": SUPPLIER_API_KEY,
        "product_id": product_id,
        "user_id": user_id,
        "zone_id": zone_id
    }
    try:
        response = requests.post(SUPPLIER_TOPUP_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            res = response.json()
            if res.get("status") == "success" or res.get("code") == 200:
                return True, res.get("order_id", "N/A")
            else:
                return False, res.get("message", "Supplier rejection")
    except Exception as e:
        print("Supplier API Error:", e)
    return False, "Connection Error"

# ==========================================
# 3. ADMIN PANEL FUNCTIONS (កំណត់ចំណេញ >= $0.01)
# ==========================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID and message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ អ្នកគ្មានសិទ្ធិចូលប្រើប្រាស់ Admin Panel ឡើយ!")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    status_text = "🔴 បិទផ្អាក (Maintenance)" if system_status["maintenance"] else "🟢 បើកដំណើរការ"
    
    btn_toggle = types.InlineKeyboardButton(f"ប្រព័ន្ធ: {status_text}", callback_data="admin_toggle_system")
    btn_set_margin = types.InlineKeyboardButton(f"💵 កំណត់តម្លៃចំណេញ (បច្ចុប្បន្ន: +${profit_margin:.2f})", callback_data="admin_set_margin")
    btn_rates = types.InlineKeyboardButton("💎 មើលតារាងតម្លៃលក់សរុប", callback_data="admin_view_rates")
    
    markup.add(btn_toggle, btn_set_margin, btn_rates)
    
    bot.send_message(
        message.chat.id, 
        f"⚙️ **ADMIN PANEL DASHBOARD**\n\n"
        f"• ស្ថានភាពប្រព័ន្ធ: {status_text}\n"
        f"• តម្លៃចំណេញបន្ថែម: `+${profit_margin:.2f}`\n\n"
        f"សូមជ្រើសរើសមុខងារខាងក្រោម៖", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_callbacks(call):
    global profit_margin
    if call.from_user.id != ADMIN_ID and call.message.chat.id != ADMIN_ID:
        return

    if call.data == "admin_toggle_system":
        system_status["maintenance"] = not system_status["maintenance"]
        status_str = "🔴 បិទផ្អាក" if system_status["maintenance"] else "🟢 បើកដំណើរការ"
        bot.answer_callback_query(call.id, f"ប្រព័ន្ធត្រូវប្តូរទៅ: {status_str}")
        admin_panel(call.message)

    elif call.data == "admin_set_margin":
        msg = bot.send_message(
            call.message.chat.id, 
            "សូមវាយបញ្ចូលចំនួនទឹកប្រាក់ចំណេញចាប់ពី **$0.01** ឡើងទៅ\n(ឧទាហរណ៍៖ `0.01`, `0.02`, `0.05`, `0.10`)៖", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_update_margin)

    elif call.data == "admin_view_rates":
        rate_text = f"💎 **តារាងតម្លៃលក់ (តម្លៃដើម + ចំណេញ ${profit_margin:.2f})៖**\n\n"
        for key, pack in BASE_PACKS.items():
            sell_p = get_selling_price(pack["base_price"])
            rate_text += f"• {pack['name']}: `${sell_p:.2f}` (ដើម: ${pack['base_price']:.2f})\n"
        bot.send_message(call.message.chat.id, rate_text, parse_mode="Markdown")

def process_update_margin(message):
    global profit_margin
    try:
        new_margin = float(message.text.strip())
        if new_margin < 0.01:
            bot.send_message(message.chat.id, "❌ តម្លៃចំណេញត្រូវតែចាប់ពី **$0.01** ឡើងទៅ! សូមព្យាយាមម្តងទៀតដោយវាយ `/admin`", parse_mode="Markdown")
            return
        profit_margin = round(new_margin, 2)
        bot.send_message(message.chat.id, f"✅ **បានផ្លាស់ប្តូរជោគជ័យ!**\nឥឡូវនេះប្រព័ន្ធបូកចំណេញបន្ថែម: `+${profit_margin:.2f}` លើគ្រប់កញ្ចប់។", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ ការបញ្ចូលមិនត្រឹមត្រូវ! សូមបញ្ចូលជាលេខ (ឧទាហរណ៍៖ `0.01`)។")

# ==========================================
# 4. CUSTOMER INTERFACE
# ==========================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if system_status["maintenance"] and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ **ប្រព័ន្ធកំពុងរៀបចំ និងកែសម្រួល (Maintenance)!**\nសូមព្យាយាមម្តងទៀតនៅពេលក្រោយ។")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💎 ទិញ Diamond MLBB", "📞 ទាក់ទង Admin")
    bot.send_message(message.chat.id, "👋 សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ Top Up MLBB ស្វ័យប្រវត្តិ!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💎 ទិញ Diamond MLBB")
def show_packs(message):
    if system_status["maintenance"] and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ ប្រព័ន្ធកំពុងបិទផ្អាកបណ្តោះអាសន្ន!")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for pack_id, pack_info in BASE_PACKS.items():
        sell_price = get_selling_price(pack_info["base_price"])
        btn_text = f"{pack_info['name']} - ${sell_price:.2f}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{pack_id}"))
    bot.send_message(message.chat.id, "សូមជ្រើសរើសកញ្ចប់ Diamond ដែលអ្នកចង់ទិញ៖", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def ask_game_id(call):
    pack_key = call.data.replace("buy_", "")
    user_states[call.message.chat.id] = {"pack_key": pack_key}
    
    msg = bot.send_message(
        call.message.chat.id, 
        "សូមផ្ញើ **User ID និង Zone ID** របស់អ្នក\nឧទាហរណ៍៖ `12345678 1234`", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_payment_flow)

def process_payment_flow(message):
    chat_id = message.chat.id
    input_text = message.text.strip().split()
    
    if len(input_text) < 2:
        msg = bot.send_message(chat_id, "❌ ទម្រង់ ID មិនត្រឹមត្រូវ! សូមផ្ញើ User ID និង Zone ID ដកឃ្លាពីគ្នា (ឧ. `12345678 1234`):")
        bot.register_next_step_handler(msg, process_payment_flow)
        return

    user_id = input_text[0]
    zone_id = input_text[1]
    
    if chat_id not in user_states or "pack_key" not in user_states[chat_id]:
        bot.send_message(chat_id, "❌ មានបញ្ហាបច្ចេកទេស! សូមចុច /start ឡើងវិញ។")
        return

    pack_key = user_states[chat_id]["pack_key"]
    pack_data = BASE_PACKS[pack_key]
    final_price = get_selling_price(pack_data["base_price"])

    generated_md5 = f"md5_hash_{chat_id}_{int(time.time())}"

    bot.send_message(
        chat_id, 
        f"📦 **កញ្ចប់:** {pack_data['name']}\n"
        f"🎮 **Game ID:** `{user_id} ({zone_id})`\n"
        f"💰 **តម្លៃទូទាត់:** `${final_price:.2f}`\n\n"
        f"សូម Scan KHQR ដើម្បីទូទាត់ប្រាក់ (ប្រព័ន្ធកំពុងរង់ចាំការបាញ់លុយស្វ័យប្រវត្តិ)...",
        parse_mode="Markdown"
    )

    max_retries = 60
    is_paid = False
    
    for _ in range(max_retries):
        paid, _ = check_khqr_payment(generated_md5)
        if paid:
            is_paid = True
            break
        time.sleep(3)

    if is_paid:
        bot.send_message(chat_id, "✅ **ទទួលបានការទូទាត់ប្រាក់រួចរាល់!**\n⚡ ប្រព័ន្ធកំពុងបញ្ជាបាញ់ Diamond...")
        
        success, order_ref = send_supplier_topup(user_id, zone_id, pack_data["product_id"])
        
        if success:
            bot.send_message(chat_id, f"🎉 **Top Up ជោគជ័យ!**\nDiamond ចូលហ្គេមរួចរាល់។\nRef: `{order_ref}`", parse_mode="Markdown")
            bot.send_message(ADMIN_GROUP_ID, f"✅ **SUCCESS ORDER**\nUser: `{user_id} ({zone_id})`\nPack: {pack_data['name']}\nPrice: `${final_price:.2f}`\nRef: `{order_ref}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ ការទូទាត់ជោគជ័យ ប៉ុន្តែមានបញ្ហាក្នុងការបាញ់ Diamond អូតូ។ Admin នឹងចាត់ការជូនភ្លាមៗ!")
            bot.send_message(ADMIN_GROUP_ID, f"🚨 **TOPUP ERROR (MANUAL NEEDED)**\nUser: `{user_id} ({zone_id})`\nPack: {pack_data['name']}\nPrice: `${final_price:.2f}`\nError: {order_ref}", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ **អស់ពេលទូទាត់ប្រាក់!** ប្រសិនបើបានបាញ់លុយរួច សូមទាក់ទងមក Admin។")

@bot.message_handler(func=lambda m: m.text == "📞 ទាក់ទង Admin")
def contact_admin(message):
    bot.send_message(message.chat.id, "📞 សម្រាប់ជំនួយ ឬមានបញ្ហាផ្សេងៗ សូមទាក់ទង Admin ផ្ទាល់។")

bot.polling(none_stop=True)
