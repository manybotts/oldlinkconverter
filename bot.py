import json
import os
import re  # Import the regular expression module
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ✅ Configuration file
CONFIG_FILE = "config.json"

# ✅ Load settings from file (or use defaults)
def load_settings():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "redirect_url": ""  # Start with an empty redirect URL
        }

# ✅ Save settings to file
def save_settings(settings):
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f)

# ✅ Load initial settings
settings = load_settings()

# ✅ Replace with YOUR Telegram user ID
ADMIN_USER_ID = 123456789

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
        "I store the base URL for your link redirection service. 🚀\n\n"
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
        "`http://secure.tg-files.com/skyking/bot8`\n\n"
        "💡 Use this format when sending the redirect URL to the bot. The bot will automatically convert it to HTTPS.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )

# =========================== View Tutorial ===========================
@bot.on_callback_query(filters.regex("tutorial"))
async def tutorial(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "**📖 How to Use the Bot:**\n\n"
        "1️⃣ Send the **base redirect URL** to this bot.\n     Example: `http://secure.tg-files.com/skyking/bot8`\n"
        "2️⃣ The bot will store this URL, ensuring it's in HTTPS format.\n"
        "3️⃣ Your external link conversion service should use this stored URL as the base for constructing redirect links.\n\n"
        "⚙️ You can view the current configuration using the /config command.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )
# =========================== Set Redirect URL ===========================
@bot.on_message(filters.command("set_redirect_url") & filters.user(ADMIN_USER_ID))
async def set_redirect_url(client: Client, message: Message):
    await message.reply_text(
        "🔗 **Send the new redirect URL** (e.g., `http://secure.tg-files.com/skyking/bot8`)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="help")]])
    )

# =========================== View Config ===========================
@bot.on_message(filters.command("config"))
async def view_config(client: Client, message: Message):
    await message.reply_text(
        f"⚙ **Current Bot Configuration:**\n"
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
            f"🔹 **Redirect URL:** `{settings['redirect_url']}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]])
        )
    elif data == "help":
        await help_command(client, query.message)

# ====================== Handle Redirect URL Input ======================
@bot.on_message(filters.regex(r"^https?://.+") & filters.user(ADMIN_USER_ID) & ~filters.command(["start", "help", "config", "set_redirect_url"]))
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
        new_url = "https://" + new_url  # In case no protocol was given at all

    settings["redirect_url"] = new_url
    save_settings(settings)
    await message.reply_text(f"✅ **Redirect URL updated to:** `{settings['redirect_url']}`")

# =========================== Handle Unexpected Texts ===========================
@bot.on_message(filters.text & ~filters.user(ADMIN_USER_ID))
async def handle_unexpected_text(client: Client, message: Message):
    await message.reply_text("❌ **Invalid command!** Use `/help` to see available commands.  Only the administrator can set the redirect URL.")

# ✅ Start the bot
bot.run()
