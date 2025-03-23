import os
import logging
import psycopg2
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_GROUP_ID, HISTORY_GROUP_ID, DEPOSIT_WITHDRAW_GROUP_ID, DATABASE_URL

# ✅ Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Database Connection
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

# ✅ Function to Send Welcome Message
def send_welcome_message(client, chat_id):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions History", url="https://t.me/joinchat/HistoryGroupLink")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")]
    ])
    client.send_message(chat_id, "Welcome to 1xBet Mobcash Agent!", reply_markup=keyboard)

# ✅ Step 1: Start Command
@app.on_message(filters.command("start"))
def start(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Step 2: Auto Send Welcome Message When User Joins
@app.on_message(filters.new_chat_members)
def welcome_new_member(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Step 3: Resend Welcome Message After Admin Approves/Rejects Deposit/Withdraw
def notify_user_and_resend_welcome(client, user_id, text):
    client.send_message(user_id, text)
    send_welcome_message(client, user_id)

# ✅ Step 4: Auto Send Welcome Message When User Types Anything
@app.on_message(filters.text & ~filters.command(["start"]))
def auto_welcome_message(client, message):
    send_welcome_message(client, message.chat.id)

# ✅ Deposit Flow# 
# ✅ Step 1: Show Payment Methods
@app.on_callback_query(filters.regex("^deposit$"))
def deposit_start(client, callback_query):
    print("Deposit started")  # Debugging print
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bkash", callback_data="deposit_bkash")],
        [InlineKeyboardButton("Nagad", callback_data="deposit_nagad")],
        [InlineKeyboardButton("Rocket", callback_data="deposit_rocket")],
        [InlineKeyboardButton("Upay", callback_data="deposit_upay")]
    ])
    callback_query.message.edit_text("Select Payment Method:", reply_markup=keyboard)

# ✅ Step 2: Show Wallet Number & "Done" Button
@app.on_callback_query(filters.regex("^deposit_(.*)"))
def deposit_method_selected(client, callback_query):
    method = callback_query.data.split("_")[1].capitalize()
    print(f"✅ DEBUG: Payment method selected: {method}")  # Debugging print
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done", callback_data=f"deposit_done_{method.lower()}")]
    ])
    
    callback_query.message.edit_text(
        f"📌 **Selected Payment Method:** {method}\n"
        "🔢 **Wallet Number:** `01770298685`\n\n"
        "After sending the money, click **Done**.",
        reply_markup=keyboard
    )

# ✅ Step 3: Show Deposit Submission Form
@app.on_callback_query(filters.regex("^deposit_done_.*"))
def deposit_submission_form(client, callback_query):
    print(f"Deposit Done clicked: {callback_query.data}")  # Debugging print
    
    method = callback_query.data.split("_")[-1].capitalize()  # Fix indexing

    new_text = (
        f"📝 **Deposit Submission Form**\n\n"
        "🎮 **Player ID:** (Enter your Player ID)\n"
        "💰 **Amount:** (Enter deposit amount)\n"
        f"💳 **Payment Method:** {method}\n"
        "🏦 **Your Wallet Number:** (Enter your wallet number)\n"
        "🔄 **Transaction ID:** (Enter transaction ID)\n\n"
        "Click **Submit** after filling in the details."
    )

    # Prevent MESSAGE_NOT_MODIFIED error
    if callback_query.message.text != new_text:
        callback_query.message.edit_text(
            new_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Submit", callback_data=f"confirm_deposit_{method.lower()}")]
            ])
        )

# ✅ Step 4: Show Confirmation Warning Before Submission
@app.on_callback_query(filters.regex("^confirm_deposit_(.+)"))
def confirm_deposit(client, callback_query):
    method = callback_query.data.split("_")[1]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data=f"deposit_submit_{method}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_deposit")]
    ])

    callback_query.message.edit_text(
        "⚠️ **Are you sure you want to submit this deposit request?**",
        reply_markup=keyboard
    )

# ✅ Step 5: Send Deposit Request to Admins & Notify User in Deposit Group
@app.on_callback_query(filters.regex("^deposit_submit_(.+)"))
def deposit_submit(client, callback_query):
    method = callback_query.data.split("_")[1]

    admin_message = (
        f"🆕 **New Deposit Request**\n"
        f"👤 User: @{callback_query.from_user.username}\n"
        f"💳 Payment Method: {method.capitalize()}\n"
        "💰 Amount: (User entered amount)\n"
        "🏦 Wallet Number: (User entered wallet)\n"
        "🔄 Transaction ID: (User entered transaction ID)\n"
        "✅ Approve or ❌ Reject?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"confirm_approve_deposit_{callback_query.from_user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"confirm_reject_deposit_{callback_query.from_user.id}")]
    ])

    # ✅ Send request to Admin Group
    client.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

    # ✅ Notify user in Deposit/Withdraw Group
    client.send_message(DEPOSIT_GROUP_ID, f"🔄 **@{callback_query.from_user.username} Your deposit request is being processed.**")

    # ✅ Notify user personally
    callback_query.message.edit_text("✅ Your deposit request is under processing.")

# ✅ Step 6: Show Confirmation Warning Before Admin Approval or Rejection
@app.on_callback_query(filters.regex("^confirm_approve_deposit_(.+)"))
def confirm_admin_approve(client, callback_query):
    user_id = callback_query.data.split("_")[3]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Approval", callback_data=f"approve_deposit_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
    ])
    callback_query.message.edit_text(
        "⚠️ **Are you sure you want to approve this deposit request?**",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^confirm_reject_deposit_(.+)"))
def confirm_admin_reject(client, callback_query):
    user_id = callback_query.data.split("_")[3]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Rejection", callback_data=f"reject_deposit_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
    ])
    callback_query.message.edit_text(
        "⚠️ **Are you sure you want to reject this deposit request?**",
        reply_markup=keyboard
    )

# ✅ If the admin cancels the action
@app.on_callback_query(filters.regex("^cancel_action"))
def cancel_action(client, callback_query):
    callback_query.message.edit_text("✅ Action cancelled.")

# ✅ If the user cancels the deposit submission
@app.on_callback_query(filters.regex("^cancel_deposit"))
def cancel_deposit(client, callback_query):
    callback_query.message.edit_text("✅ Deposit submission cancelled.")

# ✅ Withdraw Flow
# ✅ Step 1: Start Withdrawal Process
@app.on_callback_query(filters.regex("^withdraw$"))
def withdraw_start(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next ➡️", callback_data="withdraw_next")]])
    callback_query.message.reply_text(
        "🏦 **Withdrawal Address**\nCity: Chittagong\nStreet: Dorbesh Baba",
        reply_markup=keyboard
    )

# ✅ Step 2: Show Withdrawal Methods
@app.on_callback_query(filters.regex("^withdraw_next$"))
def withdraw_submission_form(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bkash", callback_data="withdraw_method_bkash")],
        [InlineKeyboardButton("Nagad", callback_data="withdraw_method_nagad")],
        [InlineKeyboardButton("Rocket", callback_data="withdraw_method_rocket")],
        [InlineKeyboardButton("Upay", callback_data="withdraw_method_upay")]
    ])
    callback_query.message.reply_text("Select Withdrawal Method:", reply_markup=keyboard)

# ✅ Step 3: Show Withdrawal Form
@app.on_callback_query(filters.regex("^withdraw_method_(.*)"))
def withdraw_method_selected(client, callback_query):
    method = callback_query.data.split("_")[2]
    client.send_message(
        callback_query.from_user.id,
        f"📝 **Withdrawal Submission Form**\n\n"
        "Player ID: (Enter your Player ID)\n"
        "Amount: (Enter withdrawal amount)\n"
        "Withdrawal Code: (Enter code)\n"
        f"Payment Method: {method.capitalize()}\n"
        "Your Wallet Number: (Enter wallet number)\n\n"
        "Click **Confirm** before submitting.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚠️ Confirm", callback_data=f"withdraw_confirm_{method}")]])
    )

# ✅ Step 4: Show Confirmation Before Submission
@app.on_callback_query(filters.regex("^withdraw_confirm_(.*)"))
def withdraw_confirm(client, callback_query):
    method = callback_query.data.split("_")[2]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Submit", callback_data=f"withdraw_submit_{method}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdraw")]
    ])
    callback_query.message.reply_text("⚠️ Are you sure you want to submit this withdrawal request?", reply_markup=keyboard)

# ✅ Step 5: Send Withdrawal Request to Admins & Notify User in Deposit Group
@app.on_callback_query(filters.regex("^withdraw_submit_(.*)"))
def withdraw_submit(client, callback_query):
    method = callback_query.data.split("_")[2]

    admin_message = (
        f"🆕 **New Withdrawal Request**\n"
        f"👤 User: @{callback_query.from_user.username}\n"
        f"💰 Amount: (User entered amount)\n"
        f"🔄 Payment Method: {method.capitalize()}\n"
        f"🏦 Wallet Number: (User entered wallet)\n"
        "✅ Approve or ❌ Reject?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"confirm_approve_withdraw_{callback_query.from_user.id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"confirm_reject_withdraw_{callback_query.from_user.id}")]
    ])

    # ✅ Send request to Admin Group
    client.send_message(ADMIN_GROUP_ID, admin_message, reply_markup=keyboard)

    # ✅ Notify user in Deposit/Withdraw Group
    client.send_message(DEPOSIT_GROUP_ID, f"🔄 **@{callback_query.from_user.username} Your withdrawal request is being processed.**")

    # ✅ Notify user personally
    callback_query.message.reply_text("✅ Your withdrawal request is under processing.")

# ✅ Step 6: Show Confirmation Warning Before Admin Approval or Rejection
@app.on_callback_query(filters.regex("^confirm_approve_withdraw_(.*)"))
def confirm_admin_approve(client, callback_query):
    user_id = callback_query.data.split("_")[3]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Approval", callback_data=f"approve_withdraw_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
    ])
    callback_query.message.reply_text(
        "⚠️ Are you sure you want to **approve** this withdrawal request?",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^confirm_reject_withdraw_(.*)"))
def confirm_admin_reject(client, callback_query):
    user_id = callback_query.data.split("_")[3]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Rejection", callback_data=f"reject_withdraw_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
    ])
    callback_query.message.reply_text(
        "⚠️ Are you sure you want to **reject** this withdrawal request?",
        reply_markup=keyboard
    )

# ✅ Step 7: Process Admin Approval
@app.on_callback_query(filters.regex("^approve_withdraw_(.*)"))
def approve_withdraw(client, callback_query):
    user_id = int(callback_query.data.split("_")[2])
    
    # Assume withdrawal amount is retrieved from user input (to be stored in DB later)
    withdrawal_amount = 1000  # Example amount, replace with actual fetched value
    
    # Calculate 2% commission
    commission = withdrawal_amount * 0.02
    update_mobcash_balance(withdrawal_amount, commission, "withdraw")  # Function to update balance
    
    # ✅ Notify user personally
    client.send_message(user_id, "✅ Your withdrawal has been approved and processed.")
    
    # ✅ Notify user in Deposit/Withdraw Group
    client.send_message(DEPOSIT_GROUP_ID, f"✅ **@{callback_query.from_user.username} Your withdrawal has been approved!**")

    # ✅ Notify admin group
    client.send_message(ADMIN_GROUP_ID, f"✅ Withdrawal of {withdrawal_amount} approved.\n💰 2% Commission: {commission}")

# ✅ Step 8: Process Admin Rejection
@app.on_callback_query(filters.regex("^reject_withdraw_(.*)"))
def reject_withdraw(client, callback_query):
    user_id = int(callback_query.data.split("_")[2])
    
    # ✅ Notify user personally
    client.send_message(user_id, "❌ Your withdrawal request has been rejected.")
    
    # ✅ Notify user in Deposit/Withdraw Group
    client.send_message(DEPOSIT_GROUP_ID, f"❌ **@{callback_query.from_user.username} Your withdrawal request was rejected.**")

    # ✅ Notify admin group
    client.send_message(ADMIN_GROUP_ID, "❌ Withdrawal request has been rejected.")

# ✅ If the admin cancels the action
@app.on_callback_query(filters.regex("^cancel_action$"))
def cancel_action(client, callback_query):
    callback_query.message.reply_text("✅ Action cancelled.")

# ✅ If the user cancels the withdrawal submission
@app.on_callback_query(filters.regex("^cancel_withdraw$"))
def cancel_withdraw(client, callback_query):
    callback_query.message.reply_text("✅ Withdrawal submission cancelled.")

# ✅ Function to Update Mobcash Balance
def update_mobcash_balance(transaction_type, amount):
    try:
        if transaction_type == "deposit":
            cursor.execute("UPDATE mobcash_balance SET balance = balance - %s, deposit_commission = deposit_commission + (%s * 0.05) WHERE id = 1", (amount, amount))
        elif transaction_type == "withdraw":
            cursor.execute("UPDATE mobcash_balance SET balance = balance + %s, withdraw_commission = withdraw_commission + (%s * 0.02) WHERE id = 1", (amount, amount))
        
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to update Mobcash balance: {e}")

# ✅ Handle Deposit Approvals
@app.on_message(filters.command("approve_deposit") & filters.chat(ADMIN_GROUP_ID))
def approve_deposit(client, message):
    try:
        _, transaction_id, amount = message.text.split()
        amount = float(amount)

        cursor.execute("UPDATE transactions SET status = 'approved' WHERE id = %s", (transaction_id,))
        conn.commit()

        update_mobcash_balance("deposit", amount)

        message.reply_text(f"✅ Deposit of {amount} approved and Mobcash balance updated.")
    except Exception as e:
        message.reply_text("❌ Error approving deposit.")
        logger.error(f"❌ Error approving deposit: {e}")

# ✅ Handle Withdrawal Approvals
@app.on_message(filters.command("approve_withdraw") & filters.chat(ADMIN_GROUP_ID))
def approve_withdraw(client, message):
    try:
        _, transaction_id, amount = message.text.split()
        amount = float(amount)

        cursor.execute("UPDATE transactions SET status = 'approved' WHERE id = %s", (transaction_id,))
        conn.commit()

        update_mobcash_balance("withdraw", amount)

        message.reply_text(f"✅ Withdrawal of {amount} approved and Mobcash balance updated.")
    except Exception as e:
        message.reply_text("❌ Error approving withdrawal.")
        logger.error(f"❌ Error approving withdrawal: {e}")

# ✅ Check Mobcash Balance, Deposits, Withdrawals & Commissions
@app.on_message(filters.command("mobcash") & filters.chat(ADMIN_GROUP_ID))
def check_mobcash_summary(client, message):
    if str(message.from_user.id) not in ADMIN_IDS:
        message.reply_text("❌ You are not authorized to check Mobcash details.")
        return

    try:
        cursor.execute("SELECT balance, deposit_commission, withdraw_commission FROM mobcash_balance WHERE id = 1")
        balance_result = cursor.fetchone()

        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'deposit' AND status = 'approved'")
        total_deposits = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'withdraw' AND status = 'approved'")
        total_withdrawals = cursor.fetchone()[0] or 0

        if balance_result:
            current_balance, deposit_commission, withdraw_commission = balance_result

            message.reply_text(
                f"📊 **Mobcash Summary:**\n\n"
                f"💰 **Current Balance:** {current_balance}\n"
                f"📥 **Total Deposits:** {total_deposits}\n"
                f"📤 **Total Withdrawals:** {total_withdrawals}\n"
                f"🟢 **Deposit Commission (5%)**: {deposit_commission}\n"
                f"🔴 **Withdraw Commission (2%)**: {withdraw_commission}"
            )
        else:
            message.reply_text("⚠️ No balance record found.")
    except Exception as e:
        logger.error(f"❌ Error fetching mobcash summary: {e}")
        message.reply_text("❌ Failed to retrieve mobcash details. Please try again.")

# ✅ Manually Update Mobcash Balance
@app.on_message(filters.command("set_balance") & filters.chat(ADMIN_GROUP_ID))
def set_mobcash_balance(client, message):
    if str(message.from_user.id) not in ADMIN_IDS:
        message.reply_text("❌ You are not authorized to update Mobcash balance.")
        return

    try:
        _, new_balance = message.text.split()
        new_balance = float(new_balance)

        cursor.execute("UPDATE mobcash_balance SET balance = %s WHERE id = 1", (new_balance,))
        conn.commit()

        message.reply_text(f"✅ Mobcash balance updated to {new_balance}.")
    except Exception as e:
        logger.error(f"❌ Failed to update Mobcash balance: {e}")
        message.reply_text("❌ Failed to update balance. Please try again.")

# ✅ Run the Bot
app.run()
