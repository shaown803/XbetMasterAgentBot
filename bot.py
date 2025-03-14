import os
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler,  CallbackContext, MessageHandler, filters

# Load the bot token from GitHub Secrets
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = -4618214079  # Replace with your private admin group ID

# Start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to 1xBet Mobcash Bot! Use the buttons below to proceed.",
                                    reply_markup=main_menu_keyboard())

# Generate Main Menu Buttons
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton("Deposit", callback_data="deposit")],
                [InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    return InlineKeyboardMarkup(keyboard)

# Deposit function
async def deposit(update: Update, context: CallbackContext):
    await update.message.reply_text("Send your deposit details in this format:\n\n"
                                    "Player ID:\nName:\nAmount:\nWallet Number:\nPayment Method:\nTransaction ID:")

# Withdrawal function
async def withdraw(update: Update, context: CallbackContext):
    await update.message.reply_text("Send your withdrawal request in this format:\n\n"
                                    "Player ID:\nName:\nApproval Code:\nAmount:\nPayment Method:\nWallet Number:")

# Handle deposit and withdrawal requests
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"New request from {user_id}:\n\n{user_message}")
    await update.message.reply_text("Your request has been sent for approval. Please wait.")

# Main function
def main():
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("deposit", deposit))
    application.add_handler(CommandHandler("withdraw", withdraw))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
