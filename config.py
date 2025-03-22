import os
from dotenv import load_dotenv

# Load environment variables from a .env file if available
load_dotenv()

# ✅ Telegram API Credentials
API_ID = int(os.getenv("API_ID", "123456"))  # Replace with your API ID
API_HASH = os.getenv("API_HASH", "your_api_hash")  # Replace with your API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")  # Replace with your Bot Token

# ✅ Telegram Group & Admin Config
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1001234567890"))  # Replace with your Admin Group ID
HISTORY_GROUP_ID = int(os.getenv("HISTORY_GROUP_ID", "-1001234567891"))  # Replace with your History Group ID
DEPOSIT_WITHDRAW_GROUP_ID = int(os.getenv("DEPOSIT_WITHDRAW_GROUP_ID", "-1001234567892"))  # Replace with Deposit/Withdraw Group ID

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# ✅ Admin User IDs (Comma-separated list)
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "123456789,987654321").split(",")]

# ✅ Commission Rates
DEPOSIT_COMMISSION_RATE = 0.05  # 5%
WITHDRAW_COMMISSION_RATE = 0.02  # 2%