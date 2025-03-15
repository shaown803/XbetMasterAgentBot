import os
import psycopg2
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    print("❌ ERROR: Bot token is missing! Check your .env file.")
    exit(1)

if not DATABASE_URL:
    print("❌ ERROR: Database URL is missing! Check your .env file.")
    exit(1)

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
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
    print("✅ Database connected and table ensured.")
except Exception as e:
    print(f"❌ Database connection error: {e}")
    exit(1)

ADMIN_GROUP_ID = -4618214079  

WALLET_NUMBERS = {
    "Bkash": "017XXXXXXXX",
    "Nagad": "018XXXXXXXX",
    "Rocket": "019XXXXXXXX",
    "uPay": "016XXXXXXXX"
}

WITHDRAWAL_ADDRESS = "City: Chittagong\nStreet: Dorbesh Baba"

# Initialize bot
app = Application.builder().token(TOKEN).build()

async def send_welcome_message(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Deposit", callback_data="deposit")],
                [InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to 1xBet Official Mobcash Agent!", reply_markup=reply_markup)

async def deposit(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Bkash", callback_data="pm_Bkash")],
                [InlineKeyboardButton("Nagad", callback_data="pm_Nagad")],
                [InlineKeyboardButton("Rocket", callback_data="pm_Rocket")],
                [InlineKeyboardButton("uPay", callback_data="pm_uPay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Please Select Payment Method:", reply_markup=reply_markup)

async def select_payment_method(update: Update, context: CallbackContext):
    query = update.callback_query
    payment_method = query.data.split("_")[1]
    wallet_number = WALLET_NUMBERS.get(payment_method, "Not Available")
    await query.message.reply_text(f"Selected: {payment_method}\nWallet Number: `{wallet_number}`")

async def confirm_payment(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text(
        "Submit your deposit details:\n\n"
        "Player ID:\nName:\nAmount:\nWallet Number:\nTransaction ID:"
    )

async def handle_deposit_submission(update: Update, context: CallbackContext):
    message = update.message.text
    admin_message = f"🔹 **New Deposit Request**\n\n{message}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
    await update.message.reply_text("Your deposit request has been submitted for approval.")

app.add_handler(CommandHandler("start", send_welcome_message))
app.add_handler(CallbackQueryHandler(deposit, pattern="^deposit$"))
app.add_handler(CallbackQueryHandler(select_payment_method, pattern="^pm_.*$"))
app.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit_submission))

if __name__ == "__main__":
    print("✅ Bot is running...")
    app.run_polling()
