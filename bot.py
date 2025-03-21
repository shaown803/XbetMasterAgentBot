import os
import logging
import psycopg2
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_GROUP_ID, DATABASE_URL

# ✅ Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Database Connection (with error handling)
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    logger.info("✅ Database connection established successfully.")

    # ✅ Create transactions table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            player_id VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            wallet_number VARCHAR(50) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            transaction_id VARCHAR(100) UNIQUE NOT NULL,
            type VARCHAR(10) CHECK (type IN ('deposit', 'withdraw')) NOT NULL,
            status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending'
        );
    """)
    conn.commit()
    logger.info("✅ Database table 'transactions' checked/created.")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    conn = None  # Prevent crashes if the DB is unavailable

# ✅ Initialize Telegram Bot
bot = Client(
    "mobcash_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

logger.info("✅ Bot initialized successfully.")

# Store user selections
user_payment_method = {}
user_transaction_data = {}

# ✅ Function to send welcome message
def send_welcome_message(user_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
         InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")]
    ])
    bot.send_message(user_id, "👋 Welcome to 1xBet Mobcash Agent\nSelect an option to continue:", reply_markup=keyboard)

# ✅ Auto-Welcome New Users
@bot.on_message(filters.new_chat_members)
def welcome_new_members(client, message):
    send_welcome_message(message.chat.id)

# ✅ Start Command
@bot.on_message(filters.command("start"))
def start(client, message):
    send_welcome_message(message.chat.id)

# ✅ Deposit - Step 1: Select Payment Method
@bot.on_callback_query(filters.regex("deposit"))
def deposit(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("bKash", callback_data="pay_bKash"),
         InlineKeyboardButton("Nagad", callback_data="pay_Nagad")]
    ])
    callback_query.message.edit_text("💳 Please Select a Payment Method:", reply_markup=keyboard)

# ✅ Deposit & Withdrawal - Step 2: Show Wallet Number
@bot.on_callback_query(filters.regex(r"pay_(.*)"))
@bot.on_callback_query(filters.regex(r"withdraw_method_(.*)"))
def select_payment_method(client, callback_query):
    user_id = callback_query.message.chat.id
    method = callback_query.data.split("_")[1]
    user_transaction_data[user_id] = {"method": method}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done", callback_data="confirm_transaction")]
    ])
    callback_query.message.edit_text(f"📋 Copy the Wallet Number for your transaction:\n\n💳 **{method} Wallet:** `01770298685`\n\nClick **Done** after sending money.", reply_markup=keyboard)

# ✅ Deposit & Withdrawal - Step 3: Ask for Form
@bot.on_callback_query(filters.regex("confirm_transaction"))
def confirm_transaction(client, callback_query):
    user_id = callback_query.message.chat.id
    user_transaction_data[user_id]["awaiting_details"] = True

    transaction_type = user_transaction_data[user_id].get("type", "deposit")

    if transaction_type == "deposit":
        callback_query.message.edit_text(
            "📝 **Fill in the following details for Deposit:**\n\n"
            "**Player ID**\n"
            "**Name**\n"
            "**Amount**\n"
            "**Your Wallet Number**\n"
            "**Transaction ID**\n\n"
            "Send the details in this format."
        )
    else:
        callback_query.message.edit_text(
            "📝 **Fill in the following details for Withdrawal:**\n\n"
            "**Player ID**\n"
            "**Name**\n"
            "**Withdraw Code**\n"
            "**Amount**\n"
            "**Wallet Number**\n\n"
            "Send the details in this format."
        )

# ✅ Deposit & Withdrawal - Step 4: Store Transaction Details
@bot.on_message(filters.text & filters.private)
def collect_transaction_details(client, message):
    user_id = message.chat.id
    if user_transaction_data.get(user_id, {}).get("awaiting_details"):
        details = message.text.split("\n")

        transaction_type = user_transaction_data[user_id].get("type", "deposit")

        if transaction_type == "deposit" and len(details) < 5:
            message.reply("❌ Invalid format! Please enter details in order:\n\nPlayer ID\nName\nAmount\nYour Wallet Number\nTransaction ID")
            return
        elif transaction_type == "withdraw" and len(details) < 5:
            message.reply("❌ Invalid format! Please enter details in order:\n\nPlayer ID\nName\nWithdraw Code\nAmount\nWallet Number")
            return

        if transaction_type == "deposit":
            player_id, name, amount, wallet_number, transaction_id = details
        else:
            player_id, name, transaction_id, amount, wallet_number = details

        method = user_transaction_data[user_id]["method"]

        try:
            cursor.execute(
                "INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (player_id, name, float(amount), wallet_number, method, transaction_id, transaction_type)
            )
            conn.commit()
            message.reply(f"✅ Your {transaction_type} request has been submitted for approval.")

            admin_message = (
                f"📩 **New {transaction_type.capitalize()} Request**\n"
                f"🆔 **Player ID:** {player_id}\n"
                f"👤 **Name:** {name}\n"
                f"💵 **Amount:** {amount} BDT\n"
                f"🏦 **Payment Method:** {method}\n"
                f"📞 **Wallet Number:** {wallet_number}\n"
                f"🔢 **Transaction ID:** {transaction_id}"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{transaction_id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_{transaction_id}")]
            ])
            bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            message.reply("❌ Failed to submit request. Please try again later.")

        del user_transaction_data[user_id]

# ✅ Admin Approves Transaction
@bot.on_callback_query(filters.regex(r"approve_(.*)"))
def approve_transaction(client, callback_query):
    transaction_id = callback_query.data.split("_")[1]
    cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    callback_query.message.edit_text("✅ Transaction Approved!")

# ✅ Admin Rejects Transaction
@bot.on_callback_query(filters.regex(r"reject_(.*)"))
def reject_transaction(client, callback_query):
    transaction_id = callback_query.data.split("_")[1]
    cursor.execute("UPDATE transactions SET status = 'rejected' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    callback_query.message.edit_text("❌ Transaction Rejected.")

# ✅ Run Bot
bot.run()
