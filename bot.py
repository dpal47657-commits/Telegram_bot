import os
import re
import sqlite3
import time
import random
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ---------- ENV ----------
load_dotenv()
BOT_TOKEN = os.getenv("8308262431:AAHhhzlMX0AZLWM2oEA6aiEPmLYiCjmg0Zo")

# ---------- DB ----------
DB = "data.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        product_id TEXT PRIMARY KEY,
        title TEXT,
        current_price INTEGER,
        last_checked INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id TEXT,
        target_price INTEGER
    )
    """)

    conn.commit()
    conn.close()

# ---------- AMAZON LINK ----------
AMAZON_REGEX = r"(?:amazon\.[a-z\.]+)/.*(?:dp|gp/product)/([A-Z0-9]{10})"

def extract_product_id(url):
    match = re.search(AMAZON_REGEX, url)
    return match.group(1) if match else None

# ---------- DEMO PRICE (replace later with API) ----------
def fetch_price(product_id):
    price = random.randint(30000, 80000)
    title = f"Product {product_id}"
    return price, title

# ---------- SAVE PRODUCT ----------
def save_product(pid, title, price):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO products(product_id, title, current_price, last_checked)
    VALUES(?,?,?,?)
    ON CONFLICT(product_id) DO UPDATE SET
        title=excluded.title,
        current_price=excluded.current_price,
        last_checked=excluded.last_checked
    """, (pid, title, price, int(time.time())))

    conn.commit()
    conn.close()

# ---------- ADD ALERT ----------
def add_alert(user_id, pid, target):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO alerts(user_id, product_id, target_price)
    VALUES(?,?,?)
    """, (user_id, pid, target))

    conn.commit()
    conn.close()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "🔗 Amazon product link भेजो\n\n"
        "मैं बताऊंगा:\n"
        "💰 Current price\n"
        "🔔 Alert set करने का option"
    )

# ---------- MESSAGE ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    pid = extract_product_id(text)
    if not pid:
        await update.message.reply_text("❌ सही Amazon link भेजो")
        return

    await update.message.reply_text("⏳ Checking price...")

    price, title = fetch_price(pid)
    save_product(pid, title, price)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Alert 🔔", callback_data=f"alert:{pid}")],
        [InlineKeyboardButton("Check Again 🔄", callback_data=f"check:{pid}")]
    ])

    await update.message.reply_text(
        f"📦 {title}\n"
        f"💰 Price: ₹{price}",
        reply_markup=keyboard
    )

# ---------- BUTTON ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("alert:"):
        pid = data.split(":")[1]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT current_price FROM products WHERE product_id=?", (pid,))
        row = cur.fetchone()
        conn.close()

        if not row:
            await query.edit_message_text("❌ Product not found")
            return

        current = row[0]
        target = int(current * 0.9)

        add_alert(user_id, pid, target)

        await query.edit_message_text(
            f"🔔 Alert set!\nTarget price: ₹{target}"
        )

    elif data.startswith("check:"):
        pid = data.split(":")[1]

        price, title = fetch_price(pid)
        save_product(pid, title, price)

        await query.edit_message_text(
            f"🔄 Updated\n\n📦 {title}\n💰 Price: ₹{price}"
        )

# ---------- MAIN ----------
def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()