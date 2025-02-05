import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# ✅ Load environment variables from Heroku
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
HEROKU_APP_URL = os.getenv("HEROKU_APP_URL", "https://your-heroku-app.herokuapp.com")  # ✅ Redirector URL
BOT_IDENTIFIER = os.getenv("BOT_IDENTIFIER", "bot1")  # ✅ Unique bot identifier (e.g., "bot1")

# ✅ Initialize the bot
bot = Client(
    "LinkConverterBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Regex pattern to extract and replace links
LINK_REGEX = r"https:\/\/t\.me\/([\w\d_]+)\?start=([\w\d-]+)"

@bot.on_message(filters.private & filters.text)
async def convert_links(client: Client, message: Message):
    """ ✅ Convert old Telegram links to the new Redirector URL format """
    old_text = message.text  # Get the full message
    new_text = old_text  # Start with the same text

    # ✅ Find and replace all old links
    matches = re.findall(LINK_REGEX, old_text)
    if matches:
        for bot_username, start_param in matches:
            old_link = f"https://t.me/{bot_username}?start={start_param}"
            new_link = f"{HEROKU_APP_URL}/bot/{BOT_IDENTIFIER}/?start={start_param}"
            new_text = new_text.replace(old_link, new_link)  # Replace in text

        await message.reply_text(f"✅ **Converted Links:**\n\n{new_text}", disable_web_page_preview=True)
    else:
        await message.reply_text("❌ No valid Telegram links found in your message.")

# ✅ Start the bot
bot.run()
