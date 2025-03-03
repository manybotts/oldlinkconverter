import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import pymongo

# ✅ MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")  # Default to localhost for dev
DB_NAME = os.getenv("DB_NAME", "link_converter_bot")
client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]
settings_collection = db["settings"]

# ✅ Load settings from MongoDB (or use defaults)
def load_settings():
    settings = settings_collection.find_one({"_id": "config"})
    if not settings:
        return {
            "redirect_url": "",
            "old_bot_username": ""
        }
    # Remove the _id field, we only need our settings
    del settings["_id"]
    return settings

# ✅ Save settings to MongoDB
def save_settings(settings):
    # We use upsert=True to insert if it doesn't exist, update if it does
    settings_collection.update_one({"_id": "config"}, {"$set": settings}, upsert=True)

# ✅ Load initial settings
settings = load_settings()

# ✅ Load ALLOWED_USERS from environment variable
ALLOWED_USERS_STR = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [int(user_id.strip()) for user_id in ALLOWED_USERS_STR.split(",") if user_id.strip()]

# ✅ Check if ALLOWED_USERS is valid
if not ALLOWED_USERS:
    print("WARNING: ALLOWED_USERS environment variable not set or empty.  Bot will not allow any users to set the URL.")

# ✅ Initialize the bot
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
bot = Client("LinkConverterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# =========================== Start Command ===========================
@bot.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Help", callback_data="help")],
            [InlineKeyboardButton("⚙️ Config", callback_data="config")],
        ]
    )
    await message.reply_text(
        "👋 **Welcome to the Redirect URL Setter Bot!**\n\n"
        "I store the base URL and old bot username for your link redirection service. 🚀\n\n"
        "Use the buttons below to navigate.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# =========================== Help Command ===========================
@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 View Tutorial", callback_data="tutorial")],
            [InlineKeyboardButton("📌 Example Input", callback_data="example_input")],
            [InlineKeyboardButton("⚙️ View Config", callback_data="config")],
        ]
    )
    await message.reply_text(
        "🛠 **Bot Commands & Help:**\n\n"
        "Click a button below to learn more or configure the bot.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# =========================== View Example Input ===========================
@bot.on_callback_query(filters.regex("example_input"))
async def example_input(client: Client, query: CallbackQuery):
     await query.message.edit_text(
        "**📌 Example Input Format:**\n\n"
        "`[SEASON 1 + https://t.me/HD10SHARE888888BOT?start=Z2V0LTM2NTcwNDE1MTA1ODQzMC0zODE3MzUwMTc5NTQxNDI]`\n"
        "`[SEASON 2 + https://t.me/HD10SHARE888888BOT?start=Z2V0LTM4MjczNjk0NzEzNTEyNC0zOTg3Njc4MTQwMzA4MzY]`\n\n"
        "`[Example Channel Link + https://t.me/ExampleChannel]`\n\n"
        "💡 Paste your links in this format.  The bot will replace the base URL *only* if the bot username (without @) matches the one set in the configuration. Other lines will be preserved.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )

# =========================== View Tutorial ===========================
@bot.on_callback_query(filters.regex("tutorial"))
async def tutorial(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "**📖 How to Use the Bot:**\n\n"
        "1️⃣ **Set Configuration (Admins Only):**\n"
        "   - Use `/set_redirect_url` to set the base URL for your redirection service.\n"
        "   - Use `/set_old_bot_username` to set the username (without @) of the bot you're replacing links for.\n"
        "2️⃣ **Paste Your Links:** Paste your links (multiple lines are allowed).\n"
        "3️⃣ **Get Converted Links:** The bot will automatically convert the links (if the bot username matches) and send them back, preserving other lines.\n\n"
        "⚙️ View current configuration: /config. Only authorized users can change settings.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )
# =========================== Set Redirect URL ===========================
@bot.on_message(filters.command("set_redirect_url") & filters.user(ALLOWED_USERS))
async def set_redirect_url(client: Client, message: Message):
    await message.reply_text(
        "🔗 **Send the new redirect URL** (e.g., `http://secure.tg-files.com/skyking/bot8`)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )

# ====================== Set Old Bot Username ======================
@bot.on_message(filters.command("set_old_bot_username") & filters.user(ALLOWED_USERS))
async def set_old_bot_username(client: Client, message: Message):
    await message.reply_text(
        "🤖 **Send the username of the old bot you are replacing links for** (e.g., `HD10SHARE888888BOT`).  **Do not include the @ symbol.**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )
#Handles the old bot username
@bot.on_message(filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url","set_old_bot_username"]) & filters.regex(r"^[a-zA-Z0-9_]{5,32}$"))
async def handle_old_bot_username_input(client: Client, message:Message):
    new_username = message.text.strip()
    if new_username.startswith("@"):
        await message.reply_text("❌ **Invalid username format.** Please enter the username *without* the @ symbol.")
        return

    settings["old_bot_username"] = new_username
    save_settings(settings)
    await message.reply_text(f"✅ **Old bot username updated to:** `{settings['old_bot_username']}`")

# =========================== View Config ===========================
@bot.on_message(filters.command("config"))
async def view_config(client: Client, message: Message):
    await message.reply_text(
        f"⚙ **Current Bot Configuration:**\n"
        f"🔹 **Redirect URL:** `{settings['redirect_url']}`\n"
        f"🔹 **Old Bot Username:** `{settings['old_bot_username']}`",
        disable_web_page_preview=True
    )

# =========================== Handle Button Clicks ===========================
@bot.on_callback_query()
async def button_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "config":
        await query.message.edit_text(
            f"⚙ **Current Bot Configuration:**\n"
            f"🔹 **Redirect URL:** `{settings['redirect_url']}`\n"
            f"🔹 **Old Bot Username:** `{settings['old_bot_username']}`",
             reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Set Redirect URL", callback_data="set_redirect_url")],
                [InlineKeyboardButton("🤖 Set Old Bot Username", callback_data="set_old_bot_username")],
                [InlineKeyboardButton("🔙 Back", callback_data="help")]
            ])
        )
    elif data == "help":
        await help_command(client, query.message)
    elif data == "set_redirect_url":
        await set_redirect_url(client, query.message)
    elif data == "set_old_bot_username":
        await set_old_bot_username(client, query.message)

# ====================== Handle Redirect URL Input ======================
@bot.on_message(filters.regex(r"^https?://.+") & filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url", "set_old_bot_username"]))
async def handle_redirect_url_input(client: Client, message: Message):
    """Handles the input of the redirect URL, validates it, and saves it in https format."""
    new_url = message.text.strip()

    # More robust URL validation using a regular expression
    url_pattern = re.compile(
        r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
    )
    if not url_pattern.match(new_url):
        await message.reply_text("❌ **Invalid URL format.** Please provide a valid URL.")
        return

    # Ensure the URL is in https format
    if new_url.startswith("http://"):
        new_url = new_url.replace("http://", "https://")
    elif not new_url.startswith("https://"):
        new_url = "https://" + new_url

    settings["redirect_url"] = new_url
    save_settings(settings)
    await message.reply_text(f"✅ **Redirect URL updated to:** `{settings['redirect_url']}`")

def chunk_text(text, max_length):
    """Splits text into chunks of at most max_length."""
    chunks = []
    current_chunk = ""
    for line in text.splitlines():
        if len(current_chunk) + len(line) + 1 <= max_length:  # +1 for newline
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks
# ====================== Handle Link Conversion ======================
@bot.on_message(filters.text & filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url", "set_old_bot_username"]))
async def handle_link_conversion(client: Client, message: Message):
    """Converts multiple links from the input message."""
    input_text = message.text.strip()
    output_lines = []

    # Reload settings from the database
    global settings
    settings = load_settings()
    old_bot_username = settings["old_bot_username"]

    # Check if old_bot_username is set
    if not old_bot_username:
        await message.reply_text("❌ **Old bot username not set.** Please set it using `/set_old_bot_username`.")
        return

    # Process each line separately
    for line in input_text.splitlines():
        line = line.strip()
        match = re.search(r"\[\s*([^\]]+?)\s*\+\s*(https:\/\/t\.me\/([^?]+))\?start=([^\]\s]+)\s*\]", line)

        if match:
            text_part, full_url, extracted_username, start_parameter = match.groups()
            text_part = text_part.strip()
            extracted_username = extracted_username.strip()
            start_parameter = start_parameter.strip()

            if extracted_username == old_bot_username:
                new_url = f"{settings['redirect_url']}?start={start_parameter}"
                new_url = new_url.replace("//?start", "/?start")
                output_lines.append(f"[{text_part} + {new_url}]")
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

    output_text = "\n".join(output_lines)

    # Split the output into chunks
    max_message_length = 4096
    chunks = chunk_text(output_text, max_message_length - 100)

    for chunk in chunks:
        await message.reply_text(
            f"`{chunk}`",
            disable_web_page_preview=True
        )

# =========================== Handle Unexpected Texts ===========================
@bot.on_message(filters.text & ~filters.user(ALLOWED_USERS))
async def handle_unexpected_text(client: Client, message: Message):
    await message.reply_text("❌ **Invalid command!** Use `/help` to see available commands. Only authorized users can interact with this bot.")

# ✅ Start the bot
bot.run()
