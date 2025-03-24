import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import config  # Import config.py

# ✅ Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Initialize Bot & Dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# ✅ Function to Create Main Menu Keyboard
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
        InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("📜 Transaction History", url=config.HISTORY_GROUP_LINK),  # Use direct group link
        InlineKeyboardButton("🆘 Contact Admin", url=config.ADMIN_CONTACT)  # Use @username or group link
    )
    return keyboard

# ✅ Function to Send Welcome Message
async def send_welcome(chat_id):
    await bot.send_message(chat_id, "Welcome to 1xBet Mobcash Agent!\n\nUse the menu below to proceed.", reply_markup=main_menu())

# ✅ Step 1: Handle /start Command (Sends Welcome Message)
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Step 2: Auto Send Welcome Message When User Joins a Group
@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def welcome_new_member(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Step 3: Resend Welcome Message After Admin Approves/Rejects Deposit/Withdraw
async def notify_user_and_resend_welcome(user_id, text):
    await bot.send_message(user_id, text)
    await send_welcome(user_id)

# ✅ Step 4: Auto Send Welcome Message When User Types Anything (Except Commands)
@dp.message_handler(lambda message: not message.text.startswith('/'))
async def auto_welcome_message(message: types.Message):
    await send_welcome(message.chat.id)

# ✅ Start Bot
if __name__ == '__main__':
    logger.info("🤖 Bot is starting...")
    executor.start_polling(dp, skip_updates=True)