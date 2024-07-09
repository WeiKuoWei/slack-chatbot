import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHATGPT_TOKEN = os.getenv("CHATGPT_TOKEN")
DB_PATH = os.getenv("DB_PATH")