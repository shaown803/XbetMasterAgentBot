import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# Load bot token
TOKEN = os.getenv("BOT_TOKEN")  # Ensure BOT_TOKEN is set in environment variables
ADMIN_GROUP_ID = -4618214079  # Replace with your private admin group ID

# Initialize bot application
app = Application.builder().token(TOKEN).build()

# Start command
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Deposit", callback_data="deposit")],
                [InlineKeyboardButton("Withdraw", callback_data="withdraw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to 1xBet Mobcash Bot! Choose an option:", reply_markup=reply_markup)

# Handle button clicks
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if query.data == "deposit":
        deposit_text = "Send your deposit details in this format:\n\n"                        "Player ID:\n"                        "Name:\n"                        "Amount:\n"                        "Wallet Number:\n"                        "Payment Method:\n"                        "Transaction ID:"
        await context.bot.send_message(chat_id, deposit_text)
    elif query.data == "withdraw":
        withdraw_text = "Send your withdrawal request in this format:\n\n"                         "Player ID:\n"                         "Name:\n"                         "Approval Code:\n"                         "Amount:\n"                         "Payment Method:\n"                         "Wallet Number:"
        await context.bot.send_message(chat_id, withdraw_text)

# Handle deposit and withdrawal messages
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    admin_message = f"New request from {user_id}:\n\n{user_message}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
    await update.message.reply_text("Your request has been sent for approval. Please wait.")

# Main function
def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
