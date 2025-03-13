import telebot
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Use environment variable for security
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))  # Store this in Railway variables

bot = telebot.TeleBot(BOT_TOKEN)

# Start Command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to 1xBet Mobcash Bot! Use /deposit or /withdraw to proceed.")

# Deposit Process
@bot.message_handler(commands=['deposit'])
def deposit_request(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Submit Deposit", callback_data="deposit_form"))
    bot.send_message(message.chat.id, "Click below to submit a deposit request.", reply_markup=keyboard)

# Withdrawal Process
@bot.message_handler(commands=['withdraw'])
def withdraw_request(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Submit Withdrawal", callback_data="withdraw_form"))
    bot.send_message(message.chat.id, "Click below to submit a withdrawal request.", reply_markup=keyboard)

# Handle Button Clicks
@bot.callback_query_handler(func=lambda call: call.data in ["deposit_form", "withdraw_form"])
def handle_forms(call):
    if call.data == "deposit_form":
        bot.send_message(call.message.chat.id, "Send your deposit details in this format:\n\nPlayer ID: \nName: \nAmount: \nWallet Number: \nPayment Method: \nTransaction ID:")
    elif call.data == "withdraw_form":
        bot.send_message(call.message.chat.id, "Send your withdrawal details in this format:\n\nPlayer ID: \nName: \nApproval Code: \nAmount: \nPayment Method: \nWallet Number:")

# Forward Requests to Admin Group
@bot.message_handler(func=lambda message: message.text and any(keyword in message.text.lower() for keyword in ["player id", "amount", "wallet number"]))
def forward_to_admin_group(message):
    bot.forward_message(ADMIN_GROUP_ID, message.chat.id, message.message_id)
    bot.reply_to(message, "Your request has been sent to the admin. Please wait for approval.")

# Run the bot with error handling
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Bot crashed: {e}")
        time.sleep(5)
