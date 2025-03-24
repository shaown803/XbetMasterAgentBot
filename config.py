import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway environment variables

# ✅ Admin Group (Replace with your actual group ID)
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1001234567890"))  # Ensure it's an integer

# ✅ History Group (Replace with your actual group ID)
HISTORY_GROUP_ID = int(os.getenv("HISTORY_GROUP_ID", "-1009876543210"))  # Ensure it's an integer

# ✅ Use a direct **group link** for transaction history
HISTORY_GROUP_LINK = "https://t.me/+QoKKOZcvEH41NjJl"

# ✅ Use a direct **username or group link** for admin contact
ADMIN_CONTACT = "https://t.me/JahanAra050"

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# ✅ Mobcash Commission Rates
DEPOSIT_COMMISSION_RATE = 0.05  # 5%
WITHDRAW_COMMISSION_RATE = 0.02  # 2%