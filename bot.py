import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ✅ Load environment variables
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

# ✅ Default values (User can update via bot)
BOT_IDENTIFIER = os.getenv("BOT_IDENTIFIER", "bot1")
HEROKU_APP_URL = os.getenv("HEROKU_APP_URL", "https://your-heroku-app.herokuapp.com")

# ✅ Store settings in memory (so users can change them)
settings = {
    "bot_identifier": BOT_IDENTIFIER,
    "redirect_url": HEROKU_APP_URL
}

# ✅ Initialize the bot
bot = Client("LinkConverterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# =========================== Start Command ===========================
@bot.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    """✅ Sends a welcome message with a modern UI"""
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Help", callback_data="help")],
            [
                InlineKeyboardButton("⚙️ Config", callback_data="config"),
                InlineKeyboardButton("🔧 Set Identifier", callback_data="set_identifier")
            ],
            [InlineKeyboardButton("🔗 Set Redirect URL", callback_data="set_redirect_url")]
        ]
    )
    await message.reply_text(
        "👋 **Welcome to the Old Links Converter Bot!**\n\n"
        "I convert old Telegram bot links to modern Heroku-based redirector URLs. 🚀\n\n"
        "Use the buttons below to navigate.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# =========================== Help Command ===========================
@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """✅ Sends a list of available commands as buttons"""
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚙️ View Config", callback_data="config")],
            [
                InlineKeyboardButton("🔧 Set Identifier", callback_data="set_identifier"),
                InlineKeyboardButton("🔗 Set Redirect URL", callback_data="set_redirect_url")
            ]
        ]
    )
    await message.reply_text(
        "🛠 **Bot Commands:**\n\n"
        "Click a button below to configure the bot settings or update details.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# =========================== Set Identifier ===========================
@bot.on_message(filters.command("set_identifier"))
async def set_identifier(client: Client, message: Message):
    """✅ Allows admins to change the bot identifier"""
    if len(message.command) < 2:
        await message.reply_text("❌ **Please provide a new bot identifier!**\nExample: `/set_identifier bot2`")
        return
    settings["bot_identifier"] = message.command[1]
    await message.reply_text(f"✅ **Bot identifier updated to:** `{settings['bot_identifier']}`")

# =========================== Set Redirect URL ===========================
@bot.on_message(filters.command("set_redirect_url"))
async def set_redirect_url(client: Client, message: Message):
    """✅ Allows admins to change the redirect URL"""
    if len(message.command) < 2:
        await message.reply_text("❌ **Please provide a new redirect URL!**\nExample: `/set_redirect_url https://new-url.herokuapp.com`")
        return
    settings["redirect_url"] = message.command[1]
    await message.reply_text(f"✅ **Redirect URL updated to:** `{settings['redirect_url']}`")

# =========================== View Config ===========================
@bot.on_message(filters.command("config"))
async def view_config(client: Client, message: Message):
    """✅ Shows the current bot settings"""
    await message.reply_text(
        f"⚙ **Current Bot Configuration:**\n"
        f"🔹 **Bot Identifier:** `{settings['bot_identifier']}`\n"
        f"🔹 **Redirect URL:** `{settings['redirect_url']}`",
        disable_web_page_preview=True
    )

# =========================== Handle Button Clicks ===========================
@bot.on_callback_query()
async def button_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "config":
        await query.message.edit_text(
            f"⚙ **Current Bot Configuration:**\n"
            f"🔹 **Bot Identifier:** `{settings['bot_identifier']}`\n"
            f"🔹 **Redirect URL:** `{settings['redirect_url']}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start")]])
        )

    elif data == "set_identifier":
        await query.message.edit_text(
            "🔧 **Send the new bot identifier** (e.g., `bot2`)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="help")]])
        )

    elif data == "set_redirect_url":
        await query.message.edit_text(
            "🔗 **Send the new redirect URL** (e.g., `https://your-new-url.herokuapp.com`)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="help")]])
        )

    elif data == "help":
        await help_command(client, query.message)

    elif data == "start":
        await start(client, query.message)

# =========================== Handle Unexpected Texts ===========================
@bot.on_message(filters.text)
async def handle_unexpected_text(client: Client, message: Message):
    """✅ Handles unexpected inputs gracefully"""
    await message.reply_text("❌ **Invalid command!** Use `/help` to see available commands.")

# ✅ Start the bot
bot.run()
