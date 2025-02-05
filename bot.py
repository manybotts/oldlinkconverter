import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ✅ Load environment variables from Heroku (default values)
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

# ✅ Default values (Can be changed via commands)
BOT_IDENTIFIER = os.getenv("BOT_IDENTIFIER", "bot1")
HEROKU_APP_URL = os.getenv("HEROKU_APP_URL", "https://your-heroku-app.herokuapp.com")

# ✅ Store settings in memory (so users can change them)
settings = {
    "bot_identifier": BOT_IDENTIFIER,
    "redirect_url": HEROKU_APP_URL
}

# ✅ Initialize the bot
bot = Client("LinkConverterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    """✅ Sends a welcome message with modern UI"""
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔧 Configure Bot", callback_data="config")]]
    )
    await message.reply_text(
        f"👋 **Welcome to the Old Links Converter Bot!**\n\n"
        "I can convert old Telegram bot links to modern Heroku-based redirector URLs. 🚀\n\n"
        "Use `/help` to see available commands.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """✅ Sends a list of available commands"""
    await message.reply_text(
        "🛠 **Bot Commands:**\n"
        "`/set_identifier <new_id>` → Change bot identifier\n"
        "`/set_redirect_url <new_url>` → Update redirector URL\n"
        "`/config` → View current bot settings\n"
        "`/help` → Show this help menu",
        disable_web_page_preview=True
    )

@bot.on_message(filters.command("set_identifier"))
async def set_identifier(client: Client, message: Message):
    """✅ Allows admins to change the bot identifier"""
    if len(message.command) < 2:
        await message.reply_text("❌ **Please provide a new bot identifier!**\nExample: `/set_identifier bot2`")
        return
    settings["bot_identifier"] = message.command[1]
    await message.reply_text(f"✅ **Bot identifier updated to:** `{settings['bot_identifier']}`")

@bot.on_message(filters.command("set_redirect_url"))
async def set_redirect_url(client: Client, message: Message):
    """✅ Allows admins to change the redirect URL"""
    if len(message.command) < 2:
        await message.reply_text("❌ **Please provide a new redirect URL!**\nExample: `/set_redirect_url https://new-url.herokuapp.com`")
        return
    settings["redirect_url"] = message.command[1]
    await message.reply_text(f"✅ **Redirect URL updated to:** `{settings['redirect_url']}`")

@bot.on_message(filters.command("config"))
async def view_config(client: Client, message: Message):
    """✅ Shows the current bot settings"""
    await message.reply_text(
        f"⚙ **Current Bot Configuration:**\n"
        f"🔹 **Bot Identifier:** `{settings['bot_identifier']}`\n"
        f"🔹 **Redirect URL:** `{settings['redirect_url']}`",
        disable_web_page_preview=True
    )

@bot.on_message(filters.text)
async def handle_unexpected_text(client: Client, message: Message):
    """✅ Handles unexpected inputs gracefully"""
    await message.reply_text("❌ **Invalid command!** Use `/help` to see available commands.")

# ✅ Start the bot
bot.run()
