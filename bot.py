import os
import logging
import psycopg2
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_GROUP_ID, DATABASE_URL
)

# Setup logging
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

# Function to send welcome message
def send_welcome_message(user_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
         InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🌍 English", callback_data="lang_en"),
         InlineKeyboardButton("🌏 বাংলা", callback_data="lang_bn")]
    ])
    bot.send_message(user_id, "👋 Welcome to 1xBet Mobcash Agent\nSelect an option to continue:", reply_markup=keyboard)

# Auto-Welcome New Users
@bot.on_message(filters.new_chat_members)
def welcome_new_members(client, message):
    chat_id = message.chat.id  # Ensures message is sent in the group
    for user in message.new_chat_members:
        send_welcome_message(chat_id)  # Sends the message in the group

# Start Command (If user types /start manually)
@bot.on_message(filters.command("start"))
def start(client, message):
    chat_id = message.chat.id  # Works for both private and group chats
    send_welcome_message(chat_id)
 
# Deposit Process - Step 1 (Select Payment Method)
@bot.on_callback_query(filters.regex("deposit"))
def deposit(client, callback_query):
    user_id = callback_query.message.chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("bKash", callback_data="pay_bKash"),
         InlineKeyboardButton("Nagad", callback_data="pay_Nagad")],
        [InlineKeyboardButton("Rocket", callback_data="pay_Rocket"),
         InlineKeyboardButton("uPay", callback_data="pay_uPay")]
    ])
    callback_query.message.edit_text("💳 Please Select a Payment Method:", reply_markup=keyboard)

# Deposit Process - Step 2 (Show Wallet Number)
@bot.on_callback_query(filters.regex(r"pay_(.*)"))
def select_payment_method(client, callback_query):
    user_id = callback_query.message.chat.id
    method = callback_query.data.split("_")[1]
    user_payment_method[user_id] = method  # Store user’s selected payment method

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copy Wallet Number", callback_data="copy_wallet")],
        [InlineKeyboardButton("✅ Done", callback_data="confirm_deposit")]
    ])
    callback_query.message.edit_text(f"📋 Copy the Wallet Number for your deposit:\n\n💳 **{method} Wallet:** `01770298685`\n\nClick **Done** after sending money.", reply_markup=keyboard)

# Deposit Process - Step 3 (User Clicks Copy)
@bot.on_callback_query(filters.regex("copy_wallet"))
def copy_wallet(client, callback_query):
    callback_query.answer("✅ Wallet Number Copied!", show_alert=True)

# Deposit Process - Step 4 (User Clicks Done, Ask for Form)
@bot.on_callback_query(filters.regex("confirm_deposit"))
def confirm_deposit(client, callback_query):
    user_id = callback_query.message.chat.id
    selected_method = user_payment_method.get(user_id, "Unknown")

    callback_query.message.edit_text(
        f"📝 **Please Fill Up the Deposit Form:**\n\n"
        f"**Player ID:** ➖\n"
        f"**Name:** ➖\n"
        f"**Amount:** ➖\n"
        f"**Payment Method:** `{selected_method}` (Auto-filled)\n"
        f"**Your Wallet Number:** ➖\n"
        f"**Transaction ID:** ➖\n\n"
        f"Click **Submit** after filling details."
    )
    user_payment_method[user_id] = "awaiting_details"

# Deposit Process - Step 5 (User Submits Form)
@bot.on_message(filters.text & filters.private)
def collect_deposit_details(client, message):
    user_id = message.chat.id
    if user_payment_method.get(user_id) == "awaiting_details":
        details = message.text.split("\n")
        if len(details) < 5:
            message.reply("❌ Invalid format! Enter details in this order:\n\n"
                          "Player ID\nName\nAmount\nYour Wallet Number\nTransaction ID")
            return

        player_id, name, amount, wallet_number, transaction_id = details
        payment_method = user_payment_method.get(user_id, "Unknown")

        cursor.execute("INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type) VALUES (%s, %s, %s, %s, %s, %s, 'deposit')",
                       (player_id, name, float(amount), wallet_number, payment_method, transaction_id))
        conn.commit()

        message.reply("✅ Your deposit request has been submitted. Please wait for admin approval.")
        admin_message = (f"📩 **New Deposit Request**\n"
                         f"🆔 **Player ID:** {player_id}\n"
                         f"👤 **Name:** {name}\n"
                         f"💵 **Amount:** {amount} BDT\n"
                         f"🏦 **Payment Method:** {payment_method}\n"
                         f"📞 **Wallet Number:** {wallet_number}\n"
                         f"🔢 **Transaction ID:** {transaction_id}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{transaction_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_{transaction_id}")]
        ])
        bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)
        del user_payment_method[user_id]

# Admin Approves or Rejects Deposit
@bot.on_callback_query(filters.regex(r"approve_(.*)"))
def approve_deposit(client, callback_query):
    transaction_id = callback_query.data.split("_")[1]
    cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    callback_query.message.edit_text("✅ Deposit Approved!")
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3  # or use MySQL if needed

# Database Connection
conn = sqlite3.connect("database.db", check_same_thread=False)  
cursor = conn.cursor()

# Define user payment method dictionary
user_payment_method = {}

# Admin group where deposit requests are sent
ADMIN_GROUP_ID = -1001234567890  # Replace with your actual group ID

# Step 1: User selects payment method
@bot.on_callback_query(filters.regex("deposit"))
def deposit(client, callback_query):
    user_id = callback_query.message.chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("bKash", callback_data="pay_bKash"),
         InlineKeyboardButton("Nagad", callback_data="pay_Nagad")]
    ])
    callback_query.message.edit_text("💳 Please Select a Payment Method:", reply_markup=keyboard)

# Step 2: Show Wallet Number
@bot.on_callback_query(filters.regex(r"pay_(.*)"))
def select_payment_method(client, callback_query):
    user_id = callback_query.message.chat.id
    method = callback_query.data.split("_")[1]
    user_payment_method[user_id] = method  

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copy Wallet Number", callback_data="copy_wallet")],
        [InlineKeyboardButton("✅ Done", callback_data="confirm_deposit")]
    ])
    callback_query.message.edit_text(f"📋 Copy the Wallet Number for your deposit:\n\n💳 **{method} Wallet:** `01770298685`\n\nClick **Done** after sending money.", reply_markup=keyboard)

# Step 3: Copy Wallet Number
@bot.on_callback_query(filters.regex("copy_wallet"))
def copy_wallet(client, callback_query):
    callback_query.answer("✅ Wallet Number Copied!", show_alert=True)

# Step 4: Ask for Deposit Form
@bot.on_callback_query(filters.regex("confirm_deposit"))
def confirm_deposit(client, callback_query):
    user_id = callback_query.message.chat.id
    selected_method = user_payment_method.get(user_id, "Unknown")

    callback_query.message.edit_text(
        f"📝 **Please Fill Up the Deposit Form:**\n\n"
        f"**Player ID:** ➖\n"
        f"**Name:** ➖\n"
        f"**Amount:** ➖\n"
        f"**Your Wallet Number:** ➖\n"
        f"**Transaction ID:** ➖\n\n"
        f"Click **Submit** after filling details."
    )
    user_payment_method[user_id] = "awaiting_details"

# Step 5: User submits deposit details
@bot.on_message(filters.text & filters.private)
def collect_deposit_details(client, message):
    user_id = message.chat.id
    if user_payment_method.get(user_id) == "awaiting_details":
        details = message.text.split("\n")
        if len(details) < 5:
            message.reply("❌ Invalid format! Please send details in this format:\n\n"
                          "**Player ID**\n"
                          "**Name**\n"
                          "**Amount**\n"
                          "**Your Wallet Number**\n"
                          "**Transaction ID**")
            return

        player_id, name, amount, wallet_number, transaction_id = details
        payment_method = user_payment_method.get(user_id, "Unknown")

        try:
            cursor.execute(
                "INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type, status) VALUES (?, ?, ?, ?, ?, ?, 'deposit', 'pending')",
                (player_id, name, float(amount), wallet_number, payment_method, transaction_id)
            )
            conn.commit()
        except Exception as e:
            message.reply("❌ Database error. Please try again later.")
            print("DB Error:", e)
            return

        message.reply("✅ Your deposit request has been submitted. Please wait for admin approval.")
        admin_message = (f"📩 **New Deposit Request**\n"
                         f"🆔 **Player ID:** {player_id}\n"
                         f"👤 **Name:** {name}\n"
                         f"💵 **Amount:** {amount} BDT\n"
                         f"🏦 **Payment Method:** {payment_method}\n"
                         f"📞 **Wallet Number:** {wallet_number}\n"
                         f"🔢 **Transaction ID:** {transaction_id}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{transaction_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_{transaction_id}")]
        ])
        bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)
        del user_payment_method[user_id]

# Step 6: Admin approves deposit
@bot.on_callback_query(filters.regex(r"approve_(.*)"))
def approve_deposit(client, callback_query):
    transaction_id = callback_query.data.split("_")[1]
    try:
        cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = ?", (transaction_id,))
        conn.commit()
        callback_query.message.edit_text("✅ Deposit Approved!")
        bot.send_message(callback_query.message.chat.id, "✅ Your deposit has been approved.")
    except Exception as e:
        print("DB Error:", e)

# Step 7: Admin rejects deposit
@bot.on_callback_query(filters.regex(r"reject_(.*)"))
def reject_deposit(client, callback_query):
    transaction_id = callback_query.data.split("_")[1]
    try:
        cursor.execute("UPDATE transactions SET status = 'rejected' WHERE transaction_id = ?", (transaction_id,))
        conn.commit()
        callback_query.message.edit_text("❌ Deposit Rejected.")
        bot.send_message(callback_query.message.chat.id, "❌ Your deposit request has been rejected.")
    except Exception as e:
        print("DB Error:", e)

# Withdrawal Process - Step 2 (User Clicks Next, Show Form)
@bot.on_callback_query(filters.regex("withdraw_next"))
def withdraw_form(client, callback_query):
    user_id = callback_query.message.chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("bKash", callback_data="withdraw_method_bKash"),
         InlineKeyboardButton("Nagad", callback_data="withdraw_method_Nagad")],
        [InlineKeyboardButton("Rocket", callback_data="withdraw_method_Rocket"),
         InlineKeyboardButton("uPay", callback_data="withdraw_method_uPay")]
    ])
    user_payment_method[user_id] = {"awaiting_details": True}

    callback_query.message.edit_text(
        "📝 **Withdrawal Submission Form:**\n"
        "🆔 **Player ID:** ➖\n"
        "👤 **Name:** ➖\n"
        "🔑 **Withdraw Code:** ➖\n"
        "💵 **Amount:** ➖\n"
        "🏦 **Payment Method:** (Click Below to Select)\n"
        "📞 **Wallet Number:** ➖\n\n"
        "**Select Payment Method Below:**",
        reply_markup=keyboard
    )

# Withdrawal Process - Step 3 (User Selects Payment Method)
@bot.on_callback_query(filters.regex(r"withdraw_method_(.*)"))
def select_withdraw_method(client, callback_query):
    user_id = callback_query.message.chat.id
    method = callback_query.data.split("_")[2]
    user_payment_method[user_id]["method"] = method

    callback_query.message.edit_text(
        f"📝 **Withdrawal Submission Form:**\n"
        f"🆔 **Player ID:** ➖\n"
        f"👤 **Name:** ➖\n"
        f"🔑 **Withdraw Code:** ➖\n"
        f"💵 **Amount:** ➖\n"
        f"🏦 **Payment Method:** `{method}` ✅\n"
        f"📞 **Wallet Number:** ➖\n\n"
        "**Now enter your details in the following order:**\n"
        "**Player ID, Name, Withdraw Code, Amount, Wallet Number**"
    )
    user_payment_method[user_id]["awaiting_submission"] = True

# Withdrawal Process - Step 4 (User Submits Form)
@bot.on_message(filters.text & filters.private)
def collect_withdraw_details(client, message):
    user_id = message.chat.id
    if user_payment_method.get(user_id, {}).get("awaiting_submission"):
        details = message.text.split("\n")
        if len(details) < 5:
            message.reply("❌ Invalid format! Enter details in this order:\n\n"
                          "Player ID\nName\nWithdraw Code\nAmount\nWallet Number")
            return

        player_id, name, withdraw_code, amount, wallet_number = details
        method = user_payment_method[user_id].get("method", "Unknown")

        cursor.execute("INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type, status) VALUES (%s, %s, %s, %s, %s, %s, 'withdraw', 'pending')",
                       (player_id, name, float(amount), wallet_number, method, withdraw_code))
        conn.commit()

        message.reply("✅ Your withdrawal request has been submitted. Please wait for admin approval.")
        admin_message = (
            f"📤 **New Withdrawal Request**\n"
            f"🆔 **Player ID:** {player_id}\n"
            f"👤 **Name:** {name}\n"
            f"🔑 **Withdraw Code:** {withdraw_code}\n"
            f"💵 **Amount:** {amount} BDT\n"
            f"🏦 **Payment Method:** {method}\n"
            f"📞 **Wallet Number:** {wallet_number}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_withdraw_{withdraw_code}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_withdraw_{withdraw_code}")]
        ])
        bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

        del user_payment_method[user_id]

# Admin Approves Withdrawal
@bot.on_callback_query(filters.regex(r"approve_withdraw_(.*)"))
def approve_withdraw(client, callback_query):
    withdraw_code = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = %s", (withdraw_code,))
    conn.commit()
    
    callback_query.message.edit_text("✅ Withdrawal Approved!")
    bot.send_message(callback_query.message.chat.id, "✅ Your withdrawal has been approved.")

# Admin Rejects Withdrawal
@bot.on_callback_query(filters.regex(r"reject_withdraw_(.*)"))
def reject_withdraw(client, callback_query):
    withdraw_code = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'rejected' WHERE transaction_id = %s", (withdraw_code,))
    conn.commit()
    
    callback_query.message.edit_text("❌ Withdrawal Rejected.")
    bot.send_message(callback_query.message.chat.id, "❌ Your withdrawal request has been rejected.")
    
    # ✅ Send Welcome Message with Deposit & Withdraw Buttons
def send_welcome_message(user_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
         InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🌐 English", callback_data="lang_en"),
         InlineKeyboardButton("🌏 বাংলা", callback_data="lang_bn")]
    ])
    bot.send_message(user_id, "🏦 **Welcome to 1xBet Mobcash!**\nSelect an option below:", reply_markup=keyboard)

# ✅ Notify User: "Your Request is Under Processing"
def notify_user_processing(user_id, transaction_type):
    status_message = "⏳ Your request is under processing by the admin."
    if transaction_type == "deposit":
        bot.send_message(user_id, f"💰 **Deposit Request Submitted**\n{status_message}")
    elif transaction_type == "withdraw":
        bot.send_message(user_id, f"📤 **Withdrawal Request Submitted**\n{status_message}")

# ✅ Notify User on Approval or Rejection + Send Welcome Message Again
def notify_user_final_status(user_id, transaction_type, status):
    if status == "approved":
        bot.send_message(user_id, f"✅ **Your {transaction_type} request has been approved!**")
    else:
        bot.send_message(user_id, f"❌ **Your {transaction_type} request has been rejected!**")

    # Send Welcome Message Again After Approval/Rejection
    send_welcome_message(user_id)

# 🏦 Deposit Submission (Step 4: User Submits Deposit Form)
@bot.on_message(filters.text & filters.private)
def collect_deposit_details(client, message):
    user_id = message.chat.id
    if user_deposit_data.get(user_id, {}).get("awaiting_details"):
        details = message.text.split("\n")
        if len(details) < 5:
            message.reply("❌ **Invalid format!**\nEnter details in this order:\n\nPlayer ID\nName\nAmount\nYour Wallet Number\nTransaction ID")
            return

        player_id, name, amount, wallet_number, transaction_id = details
        method = user_deposit_data[user_id].get("method", "Unknown")

        cursor.execute("INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type, status) VALUES (%s, %s, %s, %s, %s, %s, 'deposit', 'pending')",
                       (player_id, name, float(amount), wallet_number, method, transaction_id))
        conn.commit()

        # ✅ Notify user that request is under processing
        notify_user_processing(user_id, "deposit")

        # ✅ Send request to admin panel for approval
        admin_message = (
            f"💰 **New Deposit Request**\n"
            f"🆔 **Player ID:** {player_id}\n"
            f"👤 **Name:** {name}\n"
            f"💵 **Amount:** {amount} BDT\n"
            f"🏦 **Payment Method:** {method}\n"
            f"📞 **Wallet Number:** {wallet_number}\n"
            f"🔢 **Transaction ID:** {transaction_id}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_deposit_{transaction_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_deposit_{transaction_id}")]
        ])
        bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

        del user_deposit_data[user_id]

# ✅ Admin Approves Deposit
@bot.on_callback_query(filters.regex(r"approve_deposit_(.*)"))
def approve_deposit(client, callback_query):
    transaction_id = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    
    callback_query.message.edit_text("✅ **Deposit Approved!**")
    
    # ✅ Notify User & Send Welcome Message Again
    cursor.execute("SELECT player_id FROM transactions WHERE transaction_id = %s", (transaction_id,))
    user_id = cursor.fetchone()[0]
    notify_user_final_status(user_id, "deposit", "approved")

# ❌ Admin Rejects Deposit
@bot.on_callback_query(filters.regex(r"reject_deposit_(.*)"))
def reject_deposit(client, callback_query):
    transaction_id = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'rejected' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    
    callback_query.message.edit_text("❌ **Deposit Rejected!**")
    
    # ✅ Notify User & Send Welcome Message Again
    cursor.execute("SELECT player_id FROM transactions WHERE transaction_id = %s", (transaction_id,))
    user_id = cursor.fetchone()[0]
    notify_user_final_status(user_id, "deposit", "rejected")

# 📤 Withdrawal Submission (Step 4: User Submits Withdrawal Form)
@bot.on_message(filters.text & filters.private)
def collect_withdraw_details(client, message):
    user_id = message.chat.id
    if user_withdraw_data.get(user_id, {}).get("awaiting_details"):
        details = message.text.split("\n")
        if len(details) < 6:
            message.reply("❌ **Invalid format!**\nEnter details in this order:\n\nPlayer ID\nName\nWithdraw Code\nAmount\nPayment Method\nWallet Number")
            return

        player_id, name, withdraw_code, amount, method, wallet_number = details

        cursor.execute("INSERT INTO transactions (player_id, name, amount, wallet_number, payment_method, transaction_id, type, status) VALUES (%s, %s, %s, %s, %s, %s, 'withdraw', 'pending')",
                       (player_id, name, float(amount), wallet_number, method, withdraw_code))
        conn.commit()

        # ✅ Notify user that request is under processing
        notify_user_processing(user_id, "withdraw")

        # ✅ Send request to admin panel for approval
        admin_message = (
            f"📤 **New Withdrawal Request**\n"
            f"🆔 **Player ID:** {player_id}\n"
            f"👤 **Name:** {name}\n"
            f"🔑 **Withdraw Code:** {withdraw_code}\n"
            f"💵 **Amount:** {amount} BDT\n"
            f"🏦 **Payment Method:** {method}\n"
            f"📞 **Wallet Number:** {wallet_number}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_withdraw_{withdraw_code}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_withdraw_{withdraw_code}")]
        ])
        bot.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

        del user_withdraw_data[user_id]

# ✅ Admin Approves Withdrawal
@bot.on_callback_query(filters.regex(r"approve_withdraw_(.*)"))
def approve_withdraw(client, callback_query):
    withdraw_code = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'approved' WHERE transaction_id = %s", (withdraw_code,))
    conn.commit()
    
    callback_query.message.edit_text("✅ **Withdrawal Approved!**")
    
    cursor.execute("SELECT player_id FROM transactions WHERE transaction_id = %s", (withdraw_code,))
    user_id = cursor.fetchone()[0]
    notify_user_final_status(user_id, "withdraw", "approved")

# ❌ Admin Rejects Withdrawal
@bot.on_callback_query(filters.regex(r"reject_withdraw_(.*)"))
def reject_withdraw(client, callback_query):
    withdraw_code = callback_query.data.split("_")[2]
    cursor.execute("UPDATE transactions SET status = 'rejected' WHERE transaction_id = %s", (withdraw_code,))
    conn.commit()
    
    callback_query.message.edit_text("❌ **Withdrawal Rejected!**")
    
    cursor.execute("SELECT player_id FROM transactions WHERE transaction_id = %s", (withdraw_code,))
    user_id = cursor.fetchone()[0]
    notify_user_final_status(user_id, "withdraw", "rejected")
    
# Run Bot
bot.run()
