import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = os.getenv("DB_PATH")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in .env file")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env file")

if not DB_PATH:
    raise ValueError("DB_PATH is not set in .env file")
