import os
from dotenv import load_dotenv
from bot import Bot

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DELAY = int(os.getenv("DELAY"))

main_bot = Bot()

if __name__ == "__main__":
    main_bot.run(DISCORD_TOKEN, reconnect=True)