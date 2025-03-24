from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.utils import executor
import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# ✅ Function to Create the Main Menu Buttons
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
        InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("📜 Transaction History", url=config.HISTORY_GROUP_LINK),
        InlineKeyboardButton("🆘 Contact Admin", url=config.ADMIN_CONTACT)
    )
    return keyboard

# ✅ Function to Send the Welcome Message
async def send_welcome(chat_id):
    await bot.send_message(
        chat_id,
        "Welcome to 1xBet Mobcash Agent!\n\nUse the menu below to proceed.",
        reply_markup=main_menu()
    )

# ✅ Step 1: Handle /start Command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Step 2: Auto Send Menu When a New User Joins
@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def welcome_new_member(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Step 3: Resend Welcome Message After Admin Approves/Rejects a Transaction
async def notify_user_and_resend_welcome(user_id, text):
    await bot.send_message(user_id, text)
    await send_welcome(user_id)

# ✅ Step 4: Auto Send Menu When User Types Anything
@dp.message_handler()
async def always_show_menu(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Step 5: Setup Commands for the Three-Line Menu
async def set_bot_commands(dp: Dispatcher):
    commands = [
        BotCommand(command="deposit", description="💰 Deposit"),
        BotCommand(command="withdraw", description="📤 Withdraw"),
        BotCommand(command="history", description="📜 Transaction History"),
        BotCommand(command="contact_admin", description="🆘 Contact Admin"),
    ]
    await bot.set_my_commands(commands)

# ✅ Step 6: Handle Commands to Show Buttons
@dp.message_handler(commands=['deposit'])
async def deposit_command(message: types.Message):
    await message.answer("Click below to make a deposit:", reply_markup=main_menu())

@dp.message_handler(commands=['withdraw'])
async def withdraw_command(message: types.Message):
    await message.answer("Click below to withdraw funds:", reply_markup=main_menu())

@dp.message_handler(commands=['history'])
async def history_command(message: types.Message):
    await message.answer("📜 View transaction history here:", reply_markup=main_menu())

@dp.message_handler(commands=['contact_admin'])
async def contact_admin_command(message: types.Message):
    await message.answer("🆘 Contact an admin here:", reply_markup=main_menu())

# ✅ Start Bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_bot_commands)
