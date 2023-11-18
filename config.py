import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ACCOUNT_USERNAME = os.getenv("INSTAGRAM_USERNAME")
ACCOUNT_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("REELCIPE_TELEGRAM_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

if not ACCOUNT_USERNAME or not ACCOUNT_PASSWORD:
    raise ValueError("Instagram credentials not found in environment variables")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("REELCIPE_TELEGRAM_TOKEN not found in environment variables")
