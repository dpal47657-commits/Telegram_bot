import requests
import random
import schedule
import time
import threading
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================

BOT_TOKEN = "8520550311:AAFeKuzN3z0sEHUaplrNq8r4LTKu1EXOuPQ"
CHANNEL_ID = "@grabdeals_india"

bot = Bot(BOT_TOKEN)

# ================= TEMP MAIL =================

def generate_email():
    domains = ["1secmail.com"]
    username = "user" + str(random.randint(10000,99999))
    return username, domains[0], f"{username}@{domains[0]}"

async def mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username, domain, email = generate_email()
    context.user_data["username"] = username
    context.user_data["domain"] = domain

    await update.message.reply_text(f"📧 Your Temp Email:\n{email}")

# ================= DEAL SYSTEM =================

def get_deals():
    return [
        {"title": "Running Shoes", "price": 199, "mrp": 999, "link": "https://amzn.to/demo1"},
        {"title": "Smart Watch", "price": 299, "mrp": 1499, "link": "https://amzn.to/demo2"},
    ]

def create_caption(d):
    discount = int(((d["mrp"] - d["price"]) / d["mrp"]) * 100)
    return f"""🔥 {discount}% OFF 😱

{d['title']}

₹{d['mrp']} → ₹{d['price']}

⏳ Limited Time Deal
👉 Buy Now: {d['link']}
"""

async def deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deals = get_deals()
    for d in deals:
        await update.message.reply_text(create_caption(d))

# ================= CHANNEL POST =================

def post_to_channel():
    deals = get_deals()

    for d in deals:
        try:
            bot.send_message(chat_id=CHANNEL_ID, text=create_caption(d))
        except Exception as e:
            print("Post error:", e)

# ================= SCHEDULER =================

def run_scheduler():
    schedule.clear()
    schedule.every(10).minutes.do(post_to_channel)

    while True:
        schedule.run_pending()
        time.sleep(1)

# ================= COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Welcome to Grab Deals Bot\n\n"
        "/mail - Temp Email\n"
        "/deal - Latest Deals"
    )

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mail", mail))
    app.add_handler(CommandHandler("deal", deal))

    print("Bot running...")

    threading.Thread(target=run_scheduler, daemon=True).start()

    app.run_polling()

if __name__ == "__main__":
    main()
