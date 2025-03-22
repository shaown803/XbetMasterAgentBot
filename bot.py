import os
import logging
import psycopg2
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_GROUP_ID, DATABASE_URL, TRANSACTION_HISTORY_GROUP_ID

# ✅ Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Database Connection (with error handling)
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    logger.info("✅ Database connection established successfully.")
except psycopg2.OperationalError as e:
    logger.error(f"❌ Database connection failed: {e}")
    exit(1)  # Stop the bot if the database connection fails

# ✅ Initialize Pyrogram Bot
app = Client(
    "xbetmasteragent_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Function to send the welcome message
def send_welcome_message(client, user_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 DEPOSIT", callback_data="deposit"),
         InlineKeyboardButton("📤 WITHDRAW", callback_data="withdraw")]
    ])
    client.send_message(user_id, "👋 Welcome to 1xBet Mobcash Agent!", reply_markup=keyboard)

# ✅ /start command to send welcome message
@app.on_message(filters.command("start"))
def start(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Auto message when user joins the group
@app.on_message(filters.new_chat_members)
def welcome_new_user(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Auto-resend welcome message when user types anything
@app.on_message(filters.group & filters.text)
def auto_welcome(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Deposit Flow: User clicks "Deposit" button
@app.on_callback_query(filters.regex("deposit"))
def deposit_start(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bkash", callback_data="paymethod_bkash"),
         InlineKeyboardButton("Nagad", callback_data="paymethod_nagad")],
        [InlineKeyboardButton("Rocket", callback_data="paymethod_rocket"),
         InlineKeyboardButton("Upay", callback_data="paymethod_upay")]
    ])
    callback_query.message.edit_text("💳 **Select Payment Method:**", reply_markup=keyboard)

# ✅ Handling payment method selection
@app.on_callback_query(filters.regex("^paymethod_"))
def payment_selected(client, callback_query):
    method = callback_query.data.split("_")[1]
    wallet_number = "01770298685"  # Static wallet number for all methods
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done", callback_data=f"done_{method}")]])
    callback_query.message.edit_text(f"📌 **Copy the wallet number for your transaction:**\n`{wallet_number}`\n\nClick **Done** after completing the payment.", reply_markup=keyboard)

# ✅ After clicking "Done", ask for deposit details
@app.on_callback_query(filters.regex("^done_"))
def deposit_form(client, callback_query):
    method = callback_query.data.split("_")[1]
    client.send_message(callback_query.message.chat.id, f"📝 **Deposit Submission Form**\n\n"
                                                        f"Player ID: (Send your Player ID)\n"
                                                        f"Amount: (Send amount in BDT)\n"
                                                        f"Payment Method: {method}\n"
                                                        f"Your Wallet Number: (Send your wallet number)\n"
                                                        f"Transaction ID: (Send transaction ID)")

# ✅ Capture deposit details from user
deposit_requests = {}  # Temporary storage for deposit requests

@app.on_message(filters.private & filters.text)
def capture_deposit_data(client, message):
    user_id = message.chat.id
    if user_id not in deposit_requests:
        deposit_requests[user_id] = {"player_id": message.text}
        message.reply_text("💰 Send the deposit amount (BDT):")
    elif "amount" not in deposit_requests[user_id]:
        deposit_requests[user_id]["amount"] = message.text
        message.reply_text("📌 Send your Wallet Number:")
    elif "wallet_number" not in deposit_requests[user_id]:
        deposit_requests[user_id]["wallet_number"] = message.text
        message.reply_text("🔢 Send the Transaction ID:")
    elif "transaction_id" not in deposit_requests[user_id]:
        deposit_requests[user_id]["transaction_id"] = message.text
        deposit_details = deposit_requests.pop(user_id)

        # ✅ Send deposit request to admin group
        admin_message = (f"⚡ **New Deposit Request** ⚡\n\n"
                         f"👤 **User ID:** {user_id}\n"
                         f"🎮 **Player ID:** {deposit_details['player_id']}\n"
                         f"💰 **Amount:** {deposit_details['amount']} BDT\n"
                         f"💳 **Wallet Number:** {deposit_details['wallet_number']}\n"
                         f"🔢 **Transaction ID:** {deposit_details['transaction_id']}\n\n"
                         f"✅ Approve: /approve_{user_id}\n❌ Reject: /reject_{user_id}")
        client.send_message(ADMIN_GROUP_ID, admin_message)

        # ✅ Notify user that request is under review
        message.reply_text("⏳ Your deposit request is under processing. Please wait for admin approval.")

# ✅ Admin approval or rejection
@app.on_message(filters.command(["approve", "reject"]) & filters.chat(ADMIN_GROUP_ID))
def admin_response(client, message):
    parts = message.text.split("_")
    action = parts[0][1:]  # 'approve' or 'reject'
    user_id = int(parts[1])

    status_text = "✅ Your deposit has been **APPROVED**!" if action == "approve" else "❌ Your deposit has been **REJECTED**."
    
    # ✅ Notify user
    client.send_message(user_id, status_text)

    # ✅ Send transaction history update
    history_message = (f"📢 **New Transaction Update**\n"
                       f"👤 User: [{user_id}](tg://user?id={user_id})\n"
                       f"🔄 Type: Deposit\n"
                       f"💰 Amount: {deposit_requests[user_id]['amount']} BDT\n"
                       f"💳 Method: {deposit_requests[user_id]['wallet_number']}\n"
                       f"🔢 Transaction ID: {deposit_requests[user_id]['transaction_id']}\n"
                       f"✅ Status: {'Approved' if action == 'approve' else 'Rejected'}")
    client.send_message(TRANSACTION_HISTORY_GROUP_ID, history_message)

    # ✅ Resend welcome message
    send_welcome_message(client, user_id)

# ✅ Withdrawal Flow: User clicks "Withdraw" button
@app.on_callback_query(filters.regex("withdraw"))
def withdrawal_start(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Next", callback_data="withdraw_next")]])
    callback_query.message.edit_text("🏦 **Withdrawal Address**\n📍 City: Chittagong\n📍 Street: Dorbesh Baba\n\nClick **Next** to proceed.", reply_markup=keyboard)

# ✅ After clicking "Next", ask for withdrawal details
@app.on_callback_query(filters.regex("withdraw_next"))
def withdrawal_form(client, callback_query):
    client.send_message(callback_query.message.chat.id, "📝 **Withdrawal Submission Form**\n\n"
                                                        "Player ID: (Send your Player ID)\n"
                                                        "Amount: (Send amount in BDT)\n"
                                                        "Withdrawal Code: (Send your code)\n"
                                                        "Payment Method: (Choose from the options below)")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bkash", callback_data="withdraw_method_bkash"),
         InlineKeyboardButton("Nagad", callback_data="withdraw_method_nagad")],
        [InlineKeyboardButton("Rocket", callback_data="withdraw_method_rocket"),
         InlineKeyboardButton("Upay", callback_data="withdraw_method_upay")]
    ])
    client.send_message(callback_query.message.chat.id, "🔽 **Select Payment Method:**", reply_markup=keyboard)

# ✅ Capture withdrawal details from user
withdraw_requests = {}  # Temporary storage for withdrawal requests

@app.on_callback_query(filters.regex("^withdraw_method_"))
def withdrawal_payment_selected(client, callback_query):
    method = callback_query.data.split("_")[2]  # Extract method name
    user_id = callback_query.message.chat.id
    withdraw_requests[user_id] = {"payment_method": method}
    client.send_message(user_id, "📌 Send your Wallet Number:")

@app.on_message(filters.private & filters.text)
def capture_withdrawal_data(client, message):
    user_id = message.chat.id
    if user_id not in withdraw_requests:
        withdraw_requests[user_id] = {"player_id": message.text}
        message.reply_text("💰 Send the withdrawal amount (BDT):")
    elif "amount" not in withdraw_requests[user_id]:
        withdraw_requests[user_id]["amount"] = message.text
        message.reply_text("🔢 Send your Withdrawal Code:")
    elif "withdrawal_code" not in withdraw_requests[user_id]:
        withdraw_requests[user_id]["withdrawal_code"] = message.text
        message.reply_text("📌 Send your Wallet Number:")
    elif "wallet_number" not in withdraw_requests[user_id]:
        withdraw_requests[user_id]["wallet_number"] = message.text
        withdrawal_details = withdraw_requests.pop(user_id)

        # ✅ Send withdrawal request to admin group
        admin_message = (f"⚡ **New Withdrawal Request** ⚡\n\n"
                         f"👤 **User ID:** {user_id}\n"
                         f"🎮 **Player ID:** {withdrawal_details['player_id']}\n"
                         f"💰 **Amount:** {withdrawal_details['amount']} BDT\n"
                         f"🔢 **Withdrawal Code:** {withdrawal_details['withdrawal_code']}\n"
                         f"💳 **Payment Method:** {withdrawal_details['payment_method']}\n"
                         f"💳 **Wallet Number:** {withdrawal_details['wallet_number']}\n\n"
                         f"✅ Approve: /approve_withdraw_{user_id}\n❌ Reject: /reject_withdraw_{user_id}")
        client.send_message(ADMIN_GROUP_ID, admin_message)

        # ✅ Notify user that request is under review
        message.reply_text("⏳ Your withdrawal request is under processing. Please wait for admin approval.")

# ✅ Admin approval or rejection
@app.on_message(filters.command(["approve_withdraw", "reject_withdraw"]) & filters.chat(ADMIN_GROUP_ID))
def admin_response(client, message):
    parts = message.text.split("_")
    action = parts[0][1:]  # 'approve_withdraw' or 'reject_withdraw'
    user_id = int(parts[2])

    status_text = "✅ Your withdrawal has been **APPROVED**!" if action == "approve_withdraw" else "❌ Your withdrawal has been **REJECTED**."
    
    # ✅ Notify user
    client.send_message(user_id, status_text)

    # ✅ Send transaction history update
    history_message = (f"📢 **New Transaction Update**\n"
                       f"👤 User: [{user_id}](tg://user?id={user_id})\n"
                       f"🔄 Type: Withdrawal\n"
                       f"💰 Amount: {withdraw_requests[user_id]['amount']} BDT\n"
                       f"💳 Method: {withdraw_requests[user_id]['payment_method']}\n"
                       f"🔢 Withdrawal Code: {withdraw_requests[user_id]['withdrawal_code']}\n"
                       f"✅ Status: {'Approved' if action == 'approve_withdraw' else 'Rejected'}")
    client.send_message(TRANSACTION_HISTORY_GROUP_ID, history_message)

    # ✅ Resend welcome message
    send_welcome_message(client, user_id)

# ✅ Run the bot
app.run()
