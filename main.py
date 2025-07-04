import logging
import json
import datetime
from persiantools.jdatetime import JalaliDate
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# تنظیمات اولیه لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# فایل‌های داده
USER_DATA_FILE = 'user_data.json'
HEZB_DATA_FILE = 'hezb_list.csv'

# بارگذاری لیست حزب‌ها
def load_hezb_list():
    hezb_list = {}
    with open(HEZB_DATA_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.strip().split(',')
            hezb_list[int(parts[0])] = {'surah': parts[1], 'ayah': parts[2]}
    return hezb_list

hezb_data = load_hezb_list()
TOTAL_HEZBS = len(hezb_data)

# ذخیره/بارگذاری داده کاربران
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

user_data = load_user_data()

# مرحله تنظیمات
waiting_for = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! لطفاً تاریخ شروع (شمسی) را وارد کن. مثال: 1403-01-01")
    waiting_for[update.message.chat_id] = 'date'

def reset(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id in user_data:
        del user_data[chat_id]
        save_user_data(user_data)
    waiting_for[chat_id] = 'date'
    update.message.reply_text("تنظیمات حذف شد. لطفاً تاریخ شروع جدید را وارد کن.")

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if chat_id not in waiting_for:
        update.message.reply_text("برای تنظیمات جدید از /reset استفاده کن.")
        return

    step = waiting_for[chat_id]

    if step == 'date':
        try:
            start_date = JalaliDate(*map(int, text.split('-'))).to_gregorian()
            user_data[chat_id] = {'start_date': str(start_date)}
            waiting_for[chat_id] = 'hezb'
            update.message.reply_text("تاریخ ثبت شد ✅\nحالا لطفاً شماره حزب شروع رو وارد کن (عدد بین 1 تا 60)")
        except:
            update.message.reply_text("فرمت تاریخ اشتباهه! مثل 1403-01-01 وارد کن.")
    elif step == 'hezb':
        try:
            hezb_number = int(text)
            if 1 <= hezb_number <= TOTAL_HEZBS:
                user_data[chat_id]['hezb_start'] = hezb_number
                save_user_data(user_data)
                del waiting_for[chat_id]
                update.message.reply_text("تنظیمات ذخیره شد ✅\nاز دستور /hezb_today برای مشاهده حزب امروز استفاده کن.")
            else:
                update.message.reply_text("عدد باید بین 1 تا 60 باشه.")
        except:
            update.message.reply_text("لطفاً فقط یک عدد وارد کن.")

def get_hezb_number(start_date_str, start_hezb, day_offset):
    start_date = datetime.date.fromisoformat(start_date_str)
    today = datetime.date.today()
    delta = (today - start_date).days + day_offset
    hezb_number = ((start_hezb - 1 + delta) % TOTAL_HEZBS) + 1
    return hezb_number

def get_hezb_text(hezb_number):
    data = hezb_data.get(hezb_number, {})
    return f"📖 حزب {hezb_number}:\nاز سوره {data.get('surah')}، آیه {data.get('ayah')}"

def hezb_today(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("لطفاً اول تنظیمات را انجام دهید با دستور /start")
        return
    n = get_hezb_number(user_data[chat_id]['start_date'], user_data[chat_id]['hezb_start'], 0)
    update.message.reply_text(get_hezb_text(n))

def hezb_tomorrow(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("لطفاً اول تنظیمات را انجام دهید با دستور /start")
        return
    n = get_hezb_number(user_data[chat_id]['start_date'], user_data[chat_id]['hezb_start'], 1)
    update.message.reply_text(get_hezb_text(n))

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN") or "توکن اینجا بذار اگر نمی‌خوای از env استفاده کنی"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("reset", reset))
    dp.add_handler(CommandHandler("hezb_today", hezb_today))
    dp.add_handler(CommandHandler("hezb_tomorrow", hezb_tomorrow))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
