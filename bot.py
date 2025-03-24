import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import config

# ✅ Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Initialize bot and dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ✅ Deposit states
class DepositForm(StatesGroup):
    player_id = State()
    amount = State()
    wallet_number = State()
    transaction_id = State()
    confirmation = State()

# ✅ Main Menu
def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("💰 Deposit", "💳 Withdraw")
    keyboard.add("📜 Transaction History", "📞 Contact Admin")
    return keyboard

# ✅ Deposit Menu
def deposit_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📌 BKASH", callback_data="bkash"),
        InlineKeyboardButton("📌 NAGAD", callback_data="nagad"),
        InlineKeyboardButton("📌 ROCKET", callback_data="rocket"),
        InlineKeyboardButton("📌 UPAY", callback_data="upay"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    )
    return keyboard

# ✅ Handle /start command
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "👋 Welcome to **1xBet Mobcash Agent**!\n\n"
        "Here’s what you can do:\n"
        "📌 **Deposit Funds**\n"
        "📌 **Withdraw Funds**\n"
        "📌 **Check Transaction History**\n"
        "📌 **Contact Admin**\n\n"
        "Choose an option below:"
    )
    await message.answer(welcome_text, reply_markup=main_menu())

# ✅ Handle Deposit Button Click
@dp.message_handler(lambda message: message.text == "💰 Deposit")
async def show_deposit_methods(message: types.Message):
    await message.answer("Select a payment method:", reply_markup=deposit_menu())

# ✅ Display wallet number based on selection
async def show_wallet_number(callback_query: types.CallbackQuery):
    method = callback_query.data.upper()
    message_text = f"✅ **{method} Wallet Number**\n" \
                   f"Copy the number and send money:\n" \
                   f"**01770298685**\n\n" \
                   f"Click **DONE** after sending money."
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ DONE", callback_data=f"done_{method.lower()}"))
    await callback_query.message.edit_text(message_text, reply_markup=keyboard)

# ✅ Handle deposit selection
@dp.callback_query_handler(lambda query: query.data in ["bkash", "nagad", "rocket", "upay"])
async def handle_deposit_selection(callback_query: types.CallbackQuery):
    await show_wallet_number(callback_query)

# ✅ Handle "DONE" button click
@dp.callback_query_handler(lambda query: query.data.startswith("done_"))
async def start_deposit_form(callback_query: types.CallbackQuery, state: FSMContext):
    payment_method = callback_query.data.split("_")[1]
    await state.update_data(payment_method=payment_method)
    
    # Ask for Player ID
    await bot.send_message(callback_query.from_user.id, "1️⃣ Send your **Player ID**:")
    
    await DepositForm.player_id.set()

# ✅ Step 1: Collect Player ID
@dp.message_handler(state=DepositForm.player_id)
async def process_player_id(message: types.Message, state: FSMContext):
    await state.update_data(player_id=message.text)
    await message.answer("2️⃣ Enter the deposit amount (in BDT):")
    await DepositForm.amount.set()

# ✅ Step 2: Collect Deposit Amount
@dp.message_handler(state=DepositForm.amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await message.answer("4️⃣ Enter the **wallet number** you sent money from:")
    await DepositForm.wallet_number.set()

# ✅ Step 3: Collect Wallet Number
@dp.message_handler(state=DepositForm.wallet_number)
async def process_wallet_number(message: types.Message, state: FSMContext):
    await state.update_data(wallet_number=message.text)
    await message.answer("5️⃣ Send the **Transaction ID** from your payment receipt:")
    await DepositForm.transaction_id.set()

# ✅ Step 4: Collect Transaction ID
@dp.message_handler(state=DepositForm.transaction_id)
async def process_transaction_id(message: types.Message, state: FSMContext):
    await state.update_data(transaction_id=message.text)
    user_data = await state.get_data()

    # Show the full form for confirmation
    confirm_text = (f"📌 **Deposit Submission**\n\n"
                    f"👤 **Player ID:** {user_data['player_id']}\n"
                    f"💰 **Amount:** {user_data['amount']} BDT\n"
                    f"🏦 **Payment Method:** {user_data['payment_method'].upper()}\n"
                    f"📞 **Wallet Number:** {user_data['wallet_number']}\n"
                    f"🆔 **Transaction ID:** {user_data['transaction_id']}\n\n"
                    f"✅ **Click SUBMIT to proceed.**")

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ SUBMIT", callback_data="submit_deposit"),
        InlineKeyboardButton("❌ CANCEL", callback_data="cancel")
    )
    await message.answer(confirm_text, reply_markup=keyboard)
    await DepositForm.confirmation.set()

# ✅ Handle Confirmation
@dp.callback_query_handler(lambda query: query.data == "submit_deposit", state=DepositForm.confirmation)
async def confirm_deposit_submission(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    # Notify user
    await bot.send_message(callback_query.from_user.id, "✅ **Your deposit request is under processing!**")

    # Send to admin group
    admin_text = (f"📌 **New Deposit Request**\n\n"
                  f"👤 **Player ID:** {user_data['player_id']}\n"
                  f"💰 **Amount:** {user_data['amount']} BDT\n"
                  f"🏦 **Payment Method:** {user_data['payment_method'].upper()}\n"
                  f"📞 **Wallet Number:** {user_data['wallet_number']}\n"
                  f"🆔 **Transaction ID:** {user_data['transaction_id']}\n\n"
                  f"✅ **Approve or Reject Below.**")

    admin_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ APPROVE", callback_data="approve_deposit"),
        InlineKeyboardButton("❌ REJECT", callback_data="reject_deposit")
    )
    await bot.send_message(config.ADMIN_GROUP_ID, admin_text, reply_markup=admin_keyboard)

    # Reset state
    await state.finish()

# ✅ Handle /cancel
@dp.callback_query_handler(lambda query: query.data == "cancel", state="*")
async def cancel_process(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer("❌ Process cancelled.", reply_markup=main_menu())

# ✅ Start bot
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)