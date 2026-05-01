import sqlite3
import time
import os
from dotenv import load_dotenv
from telegram import Bot
import random

# ---------- ENV ----------
load_dotenv()
BOT_TOKEN = os.getenv("8308262431:AAHhhzlMX0AZLWM2oEA6aiEPmLYiCjmg0Zo")

bot = Bot(token=BOT_TOKEN)

DB = "data.db"

# ---------- DEMO PRICE ----------
def fetch_price(product_id):
    # अभी demo है (random)
    # बाद में API लगानी है
    price = random.randint(30000, 80000)
    title = f"Product {product_id}"
    return price, title

# ---------- UPDATE PRODUCT ----------
def update_product(pid, price, title):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    UPDATE products
    SET current_price=?, last_checked=?
    WHERE product_id=?
    """, (price, int(time.time()), pid))

    conn.commit()
    conn.close()

# ---------- MAIN CHECK ----------
def check_prices():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # सभी products उठाओ
    cur.execute("SELECT product_id FROM products")
    products = cur.fetchall()

    for (pid,) in products:
        price, title = fetch_price(pid)

        update_product(pid, price, title)

        # alerts check करो
        cur.execute("""
        SELECT user_id, target_price
        FROM alerts
        WHERE product_id=?
        """, (pid,))
        alerts = cur.fetchall()

        for user_id, target in alerts:
            if price <= target:
                try:
                    bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"🔥 Price Drop!\n\n"
                            f"📦 {title}\n"
                            f"💰 Current: ₹{price}\n"
                            f"🎯 Target: ₹{target}\n\n"
                            f"👉 अब खरीदने का सही समय!"
                        )
                    )

                    # alert हटाओ (one-time)
                    cur.execute("""
                    DELETE FROM alerts
                    WHERE user_id=? AND product_id=?
                    """, (user_id, pid))
                    conn.commit()

                except Exception as e:
                    print("Error sending message:", e)

    conn.close()

# ---------- LOOP ----------
if __name__ == "__main__":
    print("Worker running...")

    while True:
        check_prices()
        time.sleep(1800)  # हर 30 मिनट में check