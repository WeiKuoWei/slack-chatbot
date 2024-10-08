import asyncio, uvicorn, sys, os, discord, subprocess
from discord.ext import commands
from community_apps.getMessageDiscord import DiscordBot
from backend.app import app as fastapi_app

from utlis.config import DISCORD_TOKEN


# temp
from database.crudChroma import CRUD

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Define bot and command prefix
'''could use Intents.all() instead of Intents.default()'''
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize your Discord bot class 
discord_bot = DiscordBot(bot)

# Function to run FastAPI server
async def run_fastapi():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info", reload=True)
    server = uvicorn.Server(config)
    await server.serve()

# Function to run the Discord bot
async def run_discord_bot():
    await bot.start(DISCORD_TOKEN)

# Main function to run both FastAPI and Discord bot concurrently
async def main():
    fastapi_task = asyncio.create_task(run_fastapi())
    discord_task = asyncio.create_task(run_discord_bot())

    # Run both tasks concurrently
    await asyncio.gather(fastapi_task, discord_task)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Shutting down...")


# async def load_pdfs():
#     # print current working directory
#     crud = CRUD()
#     await crud.save_pdfs("./src/services/pdf_files", "course_materials")


# if __name__ == "__main__":
#     asyncio.run(load_pdfs())


'''
this, along with the !update function, should be moved to a separate file
responsible for model initialization
'''

