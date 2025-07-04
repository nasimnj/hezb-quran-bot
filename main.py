import logging
import pandas as pd
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update

# 📌 لاگ‌ها برای بررسی خطا
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 📖 بارگذاری لیست حزب‌ها
hezb_df = pd.read_csv("hezb_list.csv")

# ✅ گرفتن اطلاعات حزب بر اساس شماره
def get_hezb_info(hezb_number):
    index = (hezb_number - 1) % len(hezb_df)
    row = hezb_df.iloc[index]
    return f"📖 حزب {row['hezb_number']} از سوره {row['surah']}، آیه {row['ayah']}"

# ✅ دستور start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! خوش اومدی به ربات حزب قرآن.\n\n"
                              "از دستورات زیر می‌تونی استفاده کنی:\n"
                              "/today - حزب امروز\n"
                              "/tomorrow - حزب فردا")

# ✅ دستور today
def today(update: Update, context: CallbackContext):
    day = datetime.now().day
    msg = get_hezb_info(day)
    update.message.reply_text(f"📌 حزب امروز ({day}‌ام ماه):\n{msg}")

# ✅ دستور tomorrow
def tomorrow(update: Update, context: CallbackContext):
    day = datetime.now().day + 1
    msg = get_hezb_info(day)
    update.message.reply_text(f"📌 حزب فردا ({day}‌ام ماه):\n{msg}")

# ✅ پیام‌های غیر از دستورات
def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("دستور نامعتبره. از /start استفاده کن.")

# ✅ راه‌اندازی ربات
def main():
    # توکن ربات از BotFather
    TOKEN = "7693112096:AAELe2KYhfi0adekfuZlkFQCyzVdJUMvaOM"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # ثبت دستورات
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("today", today))
    dp.add_handler(CommandHandler("tomorrow", tomorrow))

    # هندل پیام‌های غیر قابل شناسایی
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
