import os

# API Credentials (Must be set in Railway or .env)
API_ID = int(os.getenv("API_ID", "0"))  # Default to 0 if missing
API_HASH = os.getenv("API_HASH", "")  # Empty string if missing
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Please set it in the environment variables.")

# PostgreSQL Database URL from Railway
DATABASE_URL = os.getenv("DATABASE_URL")

# Admin Group ID
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-4618214079"))  # Replace with actual group ID

# Mobcash Limit System
MOBCASH_LIMIT = float(os.getenv("MOBCASH_LIMIT", "100000"))
DEPOSIT_COMMISSION = 0.05  # 5% Deposit Commission
WITHDRAWAL_COMMISSION = 0.02  # 2% Withdrawal Commission

# Payment Methods & Wallet Numbers
PAYMENT_METHODS = {
    "bKash": os.getenv("BKASH_WALLET", "01770298685"),
    "Nagad": os.getenv("NAGAD_WALLET", "01770298685"),
    "Rocket": os.getenv("ROCKET_WALLET", "01770298685"),
    "uPay": os.getenv("UPAY_WALLET", "01770298685")
}

# Withdrawal Address
WITHDRAWAL_ADDRESS = os.getenv("WITHDRAWAL_ADDRESS", "City: Chittagong\nStreet: Dorbesh Baba")

# Multi-Agent Support (Admin Roles)
ADMIN_ROLES = {
    "admins": [],       # Full control (approve/reject transactions, view history)
    "moderators": [],   # Can approve/reject but no access to settings
    "viewers": []       # Can only view transaction history
}

# Supported Languages (English & Bangla)
LANGUAGES = {
    "en": {
        "welcome": "Welcome to 1xBet Mobcash! Select an option below:",
        "deposit": "Deposit",
        "withdraw": "Withdraw",
        "select_payment": "Please select a payment method:",
        "wallet_number": "Send your deposit to this number: {}",
        "submit_deposit": "Submit Deposit",
        "deposit_processing": "Your deposit request is under processing.",
        "withdraw_prompt": "Enter the amount you want to withdraw:",
        "submit_withdraw": "Submit Withdrawal",
        "withdraw_processing": "Your withdrawal request is under processing.",
        "approved": "✅ Your request has been approved!",
        "rejected": "❌ Your request has been rejected."
    },
    "bn": {
        "welcome": "1xBet Mobcash এ স্বাগতম! নিচে একটি বিকল্প নির্বাচন করুন:",
        "deposit": "ডিপোজিট",
        "withdraw": "উত্তোলন",
        "select_payment": "অনুগ্রহ করে একটি পেমেন্ট পদ্ধতি নির্বাচন করুন:",
        "wallet_number": "আপনার অর্থ এই নম্বরে পাঠান: {}",
        "submit_deposit": "ডিপোজিট জমা দিন",
        "deposit_processing": "আপনার ডিপোজিট অনুরোধ প্রক্রিয়াধীন রয়েছে।",
        "withdraw_prompt": "আপনি যে পরিমাণ উত্তোলন করতে চান তা লিখুন:",
        "submit_withdraw": "উত্তোলন জমা দিন",
        "withdraw_processing": "আপনার উত্তোলন অনুরোধ প্রক্রিয়াধীন রয়েছে।",
        "approved": "✅ আপনার অনুরোধ অনুমোদিত হয়েছে!",
        "rejected": "❌ আপনার অনুরোধ প্রত্যাখ্যান করা হয়েছে।"
    }
}