import os
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# Load the bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = -4618214079  # Your private admin group ID

# Initialize bot
bot = Bot(token=TOKEN)

# Start command - Show buttons for Deposit and Withdraw
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Deposit", callback_data="deposit")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome to 1xBet Mobcash Bot! Please choose an option:", reply_markup=reply_markup)

# Handle button clicks
def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "deposit":
        query.message.reply_text("Send your deposit details in this format:\n\n"
                                 "Player ID:\nName:\nAmount:\nWallet Number:\nPayment Method:\nTransaction ID:")
    elif query.data == "withdraw":
        query.message.reply_text("Send your withdrawal request in this format:\n\n"
                                 "Player ID:\nName:\nApproval Code:\nAmount:\nPayment Method:\nWallet Number:")

# Handle deposit and withdrawal requests
def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"New request from {user_id}:\n\n{user_message}")

    update.message.reply_text("Your request has been sent for approval. Please wait.")

# Main function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler("start", start))

    # Button Clicks
    dp.add_handler(CallbackQueryHandler(button_click))

    # Messages (Handles deposit/withdraw requests)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()
    updater.idle()

# Run the bot
if __name__ == "__main__":
    main()
