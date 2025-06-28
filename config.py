# config.py
import os
from pathlib import Path

# 1. Load the .env file (searches your project root)
try:
    from dotenv import load_dotenv
    load_dotenv()   # <— this will find and read your .env
except ImportError:
    pass

# 2. Now pull your token and other settings out of os.environ
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN is missing. "
        "Make sure you have a .env in your project root (or an env-var) "
        "with a line like: BOT_TOKEN=123456:ABC-DEF…"
    )

TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")
