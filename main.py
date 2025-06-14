# main.py
import os
import json
import datetime
import pandas as pd
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv
from khayyam import JalaliDate

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Load Hezb list
try:
    hezb_df = pd.read_csv("hezb_list.csv")
    logger.info(f"Loaded {len(hezb_df)} Hezb records")
except FileNotFoundError:
    logger.error("hezb_list.csv not found. Please ensure the file exists.")
    exit(1)
except Exception as e:
    logger.error(f"Error loading hezb_list.csv: {e}")
    exit(1)

# User data storage
USERS_FILE = "users.json"

# Conversation states
ASKING_HEZB, ASKING_DATE, ASKING_HOUR = range(3)

def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding='utf-8') as f:
            json.dump({}, f)

def load_users():
    ensure_users_file()
    with open(USERS_FILE, "r", encoding='utf-8') as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "سلام! به ربات ختم قرآن روزانه خوش آمدید.\n"
        "/setup - تنظیم حزب\n"
        "/status - وضعیت\n"
        "/restart - حذف تنظیمات"
    )

def setup_start(update: Update, context: CallbackContext):
    update.message.reply_text("شماره حزب شروع خود را وارد کنید (1 تا 120):")
    return ASKING_HEZB

def get_hezb(update: Update, context: CallbackContext):
    try:
        hezb = int(update.message.text)
        if not (1 <= hezb <= 120):
            update.message.reply_text("عدد بین 1 تا 120 وارد کنید:")
            return ASKING_HEZB
        context.user_data['hezb'] = hezb
        update.message.reply_text("تاریخ شروع را وارد کنید (YYYY-MM-DD):")
        return ASKING_DATE
    except:
        update.message.reply_text("عدد نامعتبر. دوباره وارد کنید:")
        return ASKING_HEZB

def get_date(update: Update, context: CallbackContext):
    try:
        context.user_data['date'] = update.message.text
        update.message.reply_text("ساعت ارسال روزانه را وارد کنید (1 تا 23):")
        return ASKING_HOUR
    except:
        update.message.reply_text("فرمت اشتباه. دوباره وارد کنید:")
        return ASKING_DATE

def get_hour(update: Update, context: CallbackContext):
    try:
        hour = int(update.message.text)
        if not (1 <= hour <= 23):
            update.message.reply_text("عدد بین 1 تا 23 وارد کنید:")
            return ASKING_HOUR

        user_id = str(update.message.chat_id)
        users = load_users()
        users[user_id] = {
            'hezb': context.user_data['hezb'],
            'date': context.user_data['date'],
            'hour': hour,
            'username': update.message.from_user.username or "",
            'first_name': update.message.from_user.first_name or ""
        }
        save_users(users)

        update.message.reply_text("تنظیمات ذخیره شد. پیام روزانه از فردا ارسال خواهد شد.")
        return ConversationHandler.END
    except:
        update.message.reply_text("خطا. دوباره تلاش کنید:")
        return ASKING_HOUR

def cancel_setup(update: Update, context: CallbackContext):
    update.message.reply_text("تنظیمات لغو شد.")
    return ConversationHandler.END

def restart_user(update: Update, context: CallbackContext):
    users = load_users()
    uid = str(update.message.chat_id)
    if uid in users:
        del users[uid]
        save_users(users)
        update.message.reply_text("تنظیمات شما حذف شد.")
    else:
        update.message.reply_text("تنظیمی یافت نشد.")

def status(update: Update, context: CallbackContext):
    users = load_users()
    uid = str(update.message.chat_id)
    user = users.get(uid)
    if user:
        update.message.reply_text(f"تنظیمات فعلی:\nحزب: {user['hezb']}\nتاریخ: {user['date']}\nساعت: {user['hour']}")
    else:
        update.message.reply_text("تنظیمی یافت نشد. /setup را اجرا کنید.")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setup', setup_start)],
        states={
            ASKING_HEZB: [MessageHandler(Filters.text & ~Filters.command, get_hezb)],
            ASKING_DATE: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            ASKING_HOUR: [MessageHandler(Filters.text & ~Filters.command, get_hour)],
        },
        fallbacks=[CommandHandler('cancel', cancel_setup)]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('restart', restart_user))
    dp.add_handler(CommandHandler('status', status))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
