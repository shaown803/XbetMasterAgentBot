import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway environment variables

# ✅ Use a direct **group link** for transaction history
HISTORY_GROUP_LINK = "https://t.me/+QoKKOZcvEH41NjJl"

# ✅ Use a direct **username or group link** for admin contact
ADMIN_CONTACT = "https://t.me/JahanAra050"

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# ✅ Mobcash Commission Rates
DEPOSIT_COMMISSION_RATE = 0.05  # 5%
WITHDRAW_COMMISSION_RATE = 0.02  # 2%