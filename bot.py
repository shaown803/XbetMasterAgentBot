import os
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# Load the bot token from GitHub Secrets
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = -1001234567890  # Replace with your private admin group ID

# Initialize bot application
app = Application.builder().token(TOKEN).build()

# Start command
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Deposit", callback_data="deposit"),
                 InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to 1xBet Mobcash Bot! Choose an option:", reply_markup=reply_markup)

# Deposit command
async def deposit(update: Update, context: CallbackContext):
    await update.message.reply_text("Send your deposit details in this format:

"
                                    "Player ID:
Name:
Amount:
Wallet Number:
Payment Method:
Transaction ID:")

# Withdrawal command
async def withdraw(update: Update, context: CallbackContext):
    await update.message.reply_text("Send your withdrawal request in this format:

"
                                    "Player ID:
Name:
Approval Code:
Amount:
Payment Method:
Wallet Number:")

# Handle button clicks
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "deposit":
        await deposit(update, context)
    elif query.data == "withdraw":
        await withdraw(update, context)

# Handle deposit and withdrawal messages
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"New request from {user_id}:

{user_message}")
    await update.message.reply_text("Your request has been sent for approval. Please wait.")

# Main function
def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
