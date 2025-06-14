import logging
import json
import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from khayyam import JalaliDate
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# حالت‌ها
ASKING_HEZB, ASKING_DATE, ASKING_HOUR = range(3)

# مسیر فایل کاربران
USERS_FILE = "users.json"
QURAN_FILE = "hezb_list.csv"


# بارگذاری کاربران
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# ذخیره کاربران
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# بارگذاری حزب‌ها
quran_df = pd.read_csv(QURAN_FILE)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! من ربات ختم روزانه قرآن هستم. برای شروع دستور /setup را بزنید.")

def setup_start(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    users = load_users()
    if user_id in users:
        del users[user_id]
        save_users(users)
        update.message.reply_text("تنظیمات قبلی شما حذف شد.")
    update.message.reply_text("شماره حزب شروع خود را وارد کنید (بین 1 تا 120):")
    return ASKING_HEZB

def get_hezb(update: Update, context: CallbackContext):
    hezb = update.message.text.strip()
    if not hezb.isdigit() or not (1 <= int(hezb) <= 120):
        update.message.reply_text("شماره حزب باید بین 1 تا 120 باشد. دوباره وارد کنید:")
        return ASKING_HEZB
    context.user_data["hezb"] = int(hezb)
    update.message.reply_text("تاریخ شروع را وارد کنید (مثلاً 1403-03-25):")
    return ASKING_DATE

def get_date(update: Update, context: CallbackContext):
    date_str = update.message.text.strip()
    try:
        JalaliDate(*map(int, date_str.split("-")))  # بررسی اعتبار تاریخ
        context.user_data["date"] = date_str
        update.message.reply_text("ساعت ارسال روزانه را وارد کنید (مثلاً 07 یا 20):")
        return ASKING_HOUR
    except:
        update.message.reply_text("تاریخ نامعتبر است. دوباره وارد کنید (مثلاً 1403-03-25):")
        return ASKING_DATE

def get_hour(update: Update, context: CallbackContext):
    hour = update.message.text.strip()
    if not hour.isdigit() or not (0 <= int(hour) <= 23):
        update.message.reply_text("ساعت باید بین 0 تا 23 باشد. دوباره وارد کنید:")
        return ASKING_HOUR

    user_id = str(update.message.chat_id)
    users = load_users()
    users[user_id] = {
        "hezb": context.user_data["hezb"],
        "date": context.user_data["date"],
        "hour": int(hour)
    }
    save_users(users)
    update.message.reply_text("تنظیمات با موفقیت ذخیره شد. 🌟")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("فرایند تنظیم لغو شد.")
    return ConversationHandler.END

def status(update: Update, context: CallbackContext):
    users = load_users()
    uid = str(update.message.chat_id)
    user = users.get(uid)
    if user:
        msg = (
            "📊 وضعیت فعلی شما:\n"
            f"🔸 حزب: {user['hezb']}\n"
            f"📅 تاریخ شروع: {user['date']}\n"
            f"⏰ ساعت ارسال روزانه: {user['hour']}\n"
        )
        update.message.reply_text(msg)
    else:
        update.message.reply_text("⛔️ هنوز تنظیماتی انجام نداده‌اید. لطفاً دستور /setup را اجرا کنید.")

def send_daily(update: Update, context: CallbackContext):
    today = JalaliDate.today()
    users = load_users()
    for uid, user in users.items():
        try:
            start_date = JalaliDate(*map(int, user["date"].split("-")))
            delta_days = (today - start_date).days
            hezb_number = user["hezb"] + delta_days
            if hezb_number > 120:
                continue
            row = quran_df[quran_df["hezb_number"] == hezb_number]
            if row.empty:
                continue
            text = (
                f"🌙 حزب امروز شما:\n"
                f"🔹 حزب شماره {hezb_number}\n"
                f"📖 سوره: {row.iloc[0]['surah']} | آیه: {row.iloc[0]['verse']}"
            )
            context.bot.send_message(chat_id=int(uid), text=text)
        except Exception as e:
            logging.warning(f"خطا برای کاربر {uid}: {e}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start)],
        states={
            ASKING_HEZB: [MessageHandler(Filters.text & ~Filters.command, get_hezb)],
            ASKING_DATE: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            ASKING_HOUR: [MessageHandler(Filters.text & ~Filters.command, get_hour)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("send", send_daily))  # دستی اجرا کردن ارسال
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
