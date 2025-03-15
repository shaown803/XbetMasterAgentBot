
import os
import psycopg2

# Connect to PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Example: Create a table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        player_id TEXT,
        amount INTEGER,
        transaction_type TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()

print("✅ Connected to PostgreSQL and ensured transactions table exists.")

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Load bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = -4618214079  # Replace with your private admin group ID

# Wallet details for each payment method
WALLET_NUMBERS = {
    "Bkash": "017XXXXXXXX",
    "Nagad": "018XXXXXXXX",
    "Rocket": "019XXXXXXXX",
    "uPay": "016XXXXXXXX"
}

# Withdrawal address details
WITHDRAWAL_ADDRESS = "City: Chittagong\nStreet: Dorbesh Baba"

# Initialize bot application
app = Application.builder().token(TOKEN).build()

# Function to send the welcome message with buttons
async def send_welcome_message(chat_id, context):
    keyboard = [[InlineKeyboardButton("Deposit", callback_data="deposit")],
                [InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="Welcome to 1xBet Official Mobcash Agent!", reply_markup=reply_markup)

# Deposit request - Step 1: Select Payment Method
async def deposit(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Bkash", callback_data="pm_Bkash")],
                [InlineKeyboardButton("Nagad", callback_data="pm_Nagad")],
                [InlineKeyboardButton("Rocket", callback_data="pm_Rocket")],
                [InlineKeyboardButton("uPay", callback_data="pm_uPay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Please Select Payment Method:", reply_markup=reply_markup)

# Step 2: Show Wallet Number and Copy Button
async def select_payment_method(update: Update, context: CallbackContext):
    query = update.callback_query
    payment_method = query.data.split("_")[1]
    wallet_number = WALLET_NUMBERS.get(payment_method, "Not Available")

    keyboard = [[InlineKeyboardButton("Copy", callback_data=f"copy_{wallet_number}")],
                [InlineKeyboardButton("Send Money Complete", callback_data="confirm_payment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(f"Selected: {payment_method}\nWallet Number: `{wallet_number}`", reply_markup=reply_markup)

# Step 3: Confirm Payment and Show Submission Form
async def confirm_payment(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text(
        "Submit your deposit details:\n\n"
        "Player ID:\nName:\nAmount:\nWallet Number:\nTransaction ID:"
    )

# Step 4: Forward deposit request to admin for approval
async def handle_deposit_submission(update: Update, context: CallbackContext):
    message = update.message.text
    admin_message = f"🔹 **New Deposit Request**\n\n{message}"
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data="approve_deposit")],
                [InlineKeyboardButton("❌ Reject", callback_data="reject_deposit")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message, reply_markup=reply_markup)
    await update.message.reply_text("Your deposit request has been submitted for approval.")

# Withdrawal request - Step 1: Select Payment Method
async def withdraw(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Bkash", callback_data="wp_Bkash")],
                [InlineKeyboardButton("Nagad", callback_data="wp_Nagad")],
                [InlineKeyboardButton("Rocket", callback_data="wp_Rocket")],
                [InlineKeyboardButton("uPay", callback_data="wp_uPay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Please Select Payment Method:", reply_markup=reply_markup)

# Step 2: Show Withdrawal Address and Ask for Amount
async def select_withdraw_method(update: Update, context: CallbackContext):
    query = update.callback_query
    payment_method = query.data.split("_")[1]

    await query.message.reply_text(
        f"Selected: {payment_method}\n{WITHDRAWAL_ADDRESS}\n\nEnter the Amount You Want to Withdraw:"
    )

# Step 3: Show Withdrawal Completion Button
async def withdrawal_complete(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Withdrawal Complete", callback_data="withdraw_complete")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Click the button below after completing the withdrawal:", reply_markup=reply_markup)

# Step 4: Ask for Player ID, Approval Code, and Wallet Number
async def withdraw_submission(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text(
        "Submit your withdrawal details:\n\n"
        "Player ID:\nWithdraw Code:\nAmount:\nWallet Number:"
    )

# Step 5: Forward withdrawal request to admin for approval
async def handle_withdraw_submission(update: Update, context: CallbackContext):
    message = update.message.text
    admin_message = f"🔹 **New Withdrawal Request**\n\n{message}"
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data="approve_withdraw")],
                [InlineKeyboardButton("❌ Reject", callback_data="reject_withdraw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message, reply_markup=reply_markup)
    await update.message.reply_text("Your withdrawal request is under processing.")

# Admin Approval/Rejection for Deposits
async def admin_approve_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text("Deposit Request Approved.")
    await send_welcome_message(query.message.chat.id, context)

async def admin_reject_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text("Deposit Request Rejected.")
    await send_welcome_message(query.message.chat.id, context)

# Admin Approval/Rejection for Withdrawals
async def admin_approve_withdraw(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text("Withdrawal Request Approved.")
    await send_welcome_message(query.message.chat.id, context)

async def admin_reject_withdraw(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text("Withdrawal Request Rejected.")
    await send_welcome_message(query.message.chat.id, context)

# Register handlers
app.add_handler(CommandHandler("start", send_welcome_message))
app.add_handler(CallbackQueryHandler(deposit, pattern="^deposit$"))
app.add_handler(CallbackQueryHandler(select_payment_method, pattern="^pm_.*$"))
app.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit_submission))
app.add_handler(CallbackQueryHandler(withdraw, pattern="^withdraw$"))
app.add_handler(CallbackQueryHandler(select_withdraw_method, pattern="^wp_.*$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdrawal_complete))
app.add_handler(CallbackQueryHandler(withdraw_submission, pattern="^withdraw_complete$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_submission))
app.add_handler(CallbackQueryHandler(admin_approve_deposit, pattern="^approve_deposit$"))
app.add_handler(CallbackQueryHandler(admin_reject_deposit, pattern="^reject_deposit$"))
app.add_handler(CallbackQueryHandler(admin_approve_withdraw, pattern="^approve_withdraw$"))
app.add_handler(CallbackQueryHandler(admin_reject_withdraw, pattern="^reject_withdraw$"))

if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
