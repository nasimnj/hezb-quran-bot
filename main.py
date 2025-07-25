from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ... سایر import ها به‌همان صورت قبل ...

# بارگذاری لیست حزب‌ها
def load_hezb_list():
    hezb_list = {}
    with open(HEZB_DATA_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.strip().split(',')
            hezb_list[int(parts[0])] = {'surah': parts[1], 'ayah': int(parts[2])}
    return hezb_list

hezb_data = load_hezb_list()
TOTAL_HEZBS = 120

# دکمه‌های منو
keyboard = [
    ['حزب امروز 📖', 'شروع دوباره 🔄']
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# شروع تنظیمات
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! لطفاً تاریخ شروع ختم قرآن (شمسی) را وارد کن. مثال: 1403-01-01", reply_markup=reply_markup)
    waiting_for[update.message.chat_id] = 'date'

def reset(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id in user_data:
        del user_data[chat_id]
        save_user_data(user_data)
    waiting_for[chat_id] = 'date'
    update.message.reply_text("تنظیمات حذف شد. لطفاً تاریخ شروع جدید را وارد کن.", reply_markup=reply_markup)

# محاسبه شماره حزب
def get_hezb_number(start_date_str, start_hezb, day_offset):
    start_date = datetime.date.fromisoformat(start_date_str)
    today = datetime.date.today()
    delta = (today - start_date).days + day_offset
    hezb_number = ((start_hezb - 1 + delta) % TOTAL_HEZBS) + 1
    return hezb_number

# گرفتن محدوده حزب
def get_hezb_text(hezb_number):
    from_data = hezb_data.get(hezb_number)
    to_data = hezb_data.get(hezb_number + 1) if hezb_number + 1 in hezb_data else {'surah': 'الناس', 'ayah': 6}
    
    return f"📖 حزب {hezb_number}:\nاز سوره {from_data['surah']}، آیه {from_data['ayah']}\n" \
           f"تا سوره {to_data['surah']}، آیه {to_data['ayah']}"

# فرمان‌ها
def hezb_today(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("لطفاً اول تنظیمات را انجام دهید با دستور /start", reply_markup=reply_markup)
        return
    n = get_hezb_number(user_data[chat_id]['start_date'], user_data[chat_id]['hezb_start'], 0)
    update.message.reply_text(get_hezb_text(n), reply_markup=reply_markup)

def hezb_tomorrow(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("لطفاً اول تنظیمات را انجام دهید با دستور /start", reply_markup=reply_markup)
        return
    n = get_hezb_number(user_data[chat_id]['start_date'], user_data[chat_id]['hezb_start'], 1)
    update.message.reply_text(get_hezb_text(n), reply_markup=reply_markup)

def days_passed(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("لطفاً ابتدا با دستور /start تنظیمات رو انجام بده.", reply_markup=reply_markup)
        return
    start_date = datetime.date.fromisoformat(user_data[chat_id]['start_date'])
    today = datetime.date.today()
    delta_days = (today - start_date).days
    update.message.reply_text(f"📅 از شروع ختم قرآن {delta_days} روز گذشته.", reply_markup=reply_markup)

# مدیریت پیام‌ها
def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if text == "حزب امروز 📖":
        hezb_today(update, context)
        return
    elif text == "شروع دوباره 🔄":
        reset(update, context)
        return

    if chat_id not in waiting_for:
        update.message.reply_text("برای تنظیمات جدید از /reset استفاده کن.", reply_markup=reply_markup)
        return

    step = waiting_for[chat_id]

    if step == 'date':
        try:
            start_date = JalaliDate(*map(int, text.split('-'))).to_gregorian()
            user_data[chat_id] = {'start_date': str(start_date)}
            waiting_for[chat_id] = 'hezb'
            update.message.reply_text(f"تاریخ ثبت شد ✅\nحالا لطفاً شماره حزب شروع رو وارد کن (عدد بین 1 تا {TOTAL_HEZBS})", reply_markup=reply_markup)
        except:
            update.message.reply_text("❌ فرمت تاریخ اشتباهه! مثل 1403-01-01 وارد کن.", reply_markup=reply_markup)
    elif step == 'hezb':
        try:
            hezb_number = int(text)
            if 1 <= hezb_number <= TOTAL_HEZBS:
                user_data[chat_id]['hezb_start'] = hezb_number
                save_user_data(user_data)
                del waiting_for[chat_id]
                update.message.reply_text(f"تنظیمات ذخیره شد ✅\nاز دکمه ‘حزب امروز 📖’ استفاده کن.", reply_markup=reply_markup)
            else:
                update.message.reply_text(f"❌ عدد باید بین 1 تا {TOTAL_HEZBS} باشه.", reply_markup=reply_markup)
        except:
            update.message.reply_text("❌ لطفاً فقط یک عدد وارد کن.", reply_markup=reply_markup)

# اجرای ربات
def main():
    import os
    TOKEN = "توکن خودت اینجاست"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("reset", reset))
    dp.add_handler(CommandHandler("hezb_today", hezb_today))
    dp.add_handler(CommandHandler("hezb_tomorrow", hezb_tomorrow))
    dp.add_handler(CommandHandler("days_passed", days_passed))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
