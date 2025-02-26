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
            "username_redirect_pairs": []  # Initialize as an empty list
        }
    del settings["_id"]
    return settings

# ✅ Save settings to MongoDB
def save_settings(settings):
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

# ✅ State management for input
user_states = {}  # Dictionary to store user states: {user_id: "state"}

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
        "💡 Paste your links in this format.  The bot will replace the base URL *only* if the bot username (without @) matches one set in the configuration. Other lines will be preserved.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )

# =========================== View Tutorial ===========================
@bot.on_callback_query(filters.regex("tutorial"))
async def tutorial(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "**📖 How to Use the Bot:**\n\n"
        "1️⃣ **Set Configuration (Admins Only):**\n"
        "   - Use `/add_old_bot_username` to add a bot username.\n"
        "   - Use `/set_redirect_url` to set the redirect URL for a username.\n"
        "   - Use `/edit_redirect_url` to modify an existing redirect URL.\n"
        "   - Use `/delete_old_bot_username` to remove a username and its URL.\n"
        "2️⃣ **Start Conversion:** Use `/start_conversion` to begin converting links.\n"
        "3️⃣ **Paste Your Links:** Paste your links (multiple lines are allowed).\n"
        "4️⃣ **Stop Conversion:** Use `/stop_conversion` to stop converting links.\n\n"        
        "⚙️ View current configuration: /config. Only authorized users can change settings.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
        disable_web_page_preview=True
    )
# =========================== Set Redirect URL ===========================
@bot.on_message(filters.command("set_redirect_url") & filters.user(ALLOWED_USERS))
async def set_redirect_url(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "waiting_for_url" # Set the user's state
    await message.reply_text(
        "🔗 **Send the new redirect URL AND the associated old bot username, separated by a space.**\n\n"
        "Example: `http://secure.tg-files.com/skyking/bot8 HD10SHARE888888BOT`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )

# ====================== Add Old Bot Username ======================
@bot.on_message(filters.command("add_old_bot_username") & filters.user(ALLOWED_USERS))
async def add_old_bot_username(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "waiting_for_username"  # Set user's state
    await message.reply_text(
        "🤖 **Send the username of the old bot you are adding** (e.g., `HD10SHARE888888BOT`).  **Do not include the @ symbol.**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )

# ====================== Edit Redirect URL ======================
@bot.on_message(filters.command("edit_redirect_url") & filters.user(ALLOWED_USERS))
async def edit_redirect_url(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "waiting_for_edit"  # Set user's state
    await message.reply_text(
        "✏️ **Send the OLD BOT USERNAME whose redirect URL you want to edit.**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )

# ====================== Delete Old Bot Username ======================
@bot.on_message(filters.command("delete_old_bot_username") & filters.user(ALLOWED_USERS))
async def delete_old_bot_username(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "waiting_for_delete"  # Set user's state
    await message.reply_text(
        "🗑️ **Send the username of the old bot you want to DELETE.**  (This will remove both the username and its redirect URL.)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
    )

# ====================== Start/Stop Conversion ======================
@bot.on_message(filters.command("start_conversion") & filters.user(ALLOWED_USERS))
async def start_conversion_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "converting"
    await message.reply_text("✅ **Link conversion started.** Now paste your links.")

@bot.on_message(filters.command("stop_conversion") & filters.user(ALLOWED_USERS))
async def stop_conversion_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)  # Remove the state, if it exists
    await message.reply_text("🛑 **Link conversion stopped.**")

#End of Part 1 of 3
#Handles the old bot username
@bot.on_message(filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url","add_old_bot_username", "edit_redirect_url", "delete_old_bot_username"]) & filters.regex(r"^[a-zA-Z0-9_]{5,32}$"))
async def handle_old_bot_username_input(client: Client, message:Message):
    global settings
    user_id = message.from_user.id
    current_state = user_states.get(user_id)

    if current_state == "waiting_for_username":
        new_username = message.text.strip()
        if new_username.startswith("@"):
            await message.reply_text("❌ **Invalid username format.** Please enter the username *without* the @ symbol.")
            return

        # Check if the username already exists
        settings = load_settings()  # Reload settings
        for pair in settings["username_redirect_pairs"]:
            if pair["username"] == new_username:
                await message.reply_text(f"❌ **Username `{new_username}` already exists!**")
                return

        # Add the new username to the list with an empty redirect_url for now
        settings["username_redirect_pairs"].append({"username": new_username, "redirect_url": ""})
        save_settings(settings)
        await message.reply_text(f"✅ **Old bot username `{new_username}` added.**  Now use `/set_redirect_url` to set its redirect URL.")
        user_states.pop(user_id, None)  # Remove user from state tracking

    elif current_state == "waiting_for_delete":
        username_to_delete = message.text.strip()
        # Find and delete the username
        settings = load_settings()  # Reload settings
        found = False
        for i, pair in enumerate(settings["username_redirect_pairs"]):
            if pair["username"] == username_to_delete:
                del settings["username_redirect_pairs"][i]
                found = True
                break  # Exit loop after deleting

        if found:
            save_settings(settings)
            await message.reply_text(f"✅ **Username `{username_to_delete}` and its associated redirect URL have been deleted.**")
        else:
            await message.reply_text(f"❌ **Username `{username_to_delete}` not found.**")
        user_states.pop(user_id, None)

    elif current_state == "waiting_for_edit":
            username_to_edit = message.text.strip()
            settings = load_settings() #Reload settings
            found = False
            for pair in settings["username_redirect_pairs"]:
                if pair["username"] == username_to_edit:
                    user_states[user_id] = f"editing:{username_to_edit}" #Save which username to edit
                    await message.reply_text(f"📝 **Send the new redirect URL for `{username_to_edit}`:**")
                    found = True
                    break #Exit loop
            if not found:
                await message.reply_text(f"❌ **Username `{username_to_edit}` not found.**")
                user_states.pop(user_id, None) #Clear state

    else:
        # Ignore if not in the correct state
        return

@bot.on_message(filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url", "add_old_bot_username", "edit_redirect_url", "delete_old_bot_username"]))
async def handle_set_redirect_url_input(client: Client, message: Message):
    global settings
    user_id = message.from_user.id
    current_state = user_states.get(user_id)

    if current_state == "waiting_for_url":
        input_text = message.text.strip()
        parts = input_text.split()

        if len(parts) != 2:
            await message.reply_text("❌ **Invalid input.** Please provide the redirect URL and the old bot username, separated by a space.")
            return

        new_url, old_bot_username = parts
        new_url = new_url.strip()
        old_bot_username = old_bot_username.strip()

        # Validate the URL
        url_pattern = re.compile(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!$&'()*+,;=.]+$"  # Corrected Regex
        )
        if not url_pattern.match(new_url):
            await message.reply_text("❌ **Invalid URL format.** Please provide a valid URL.")
            return

        # Ensure the URL is in https format
        if new_url.startswith("http://"):
            new_url = new_url.replace("http://", "https://")
        elif not new_url.startswith("https://"):
            new_url = "https://" + new_url
        # Reload settings from the database
        settings = load_settings()
        # Find the username in the settings and update the redirect_url
        username_found = False
        for pair in settings["username_redirect_pairs"]:
            if pair["username"] == old_bot_username:
                pair["redirect_url"] = new_url
                username_found = True
                break

        if not username_found:
            await message.reply_text(f"❌ **Old bot username `{old_bot_username}` not found.**  Add it using `/add_old_bot_username` first.")
            return

        save_settings(settings)
        await message.reply_text(f"✅ **Redirect URL updated for username `{old_bot_username}` to:** `{new_url}`")
        user_states.pop(user_id, None)  # Remove user from state tracking

    elif current_state and current_state.startswith("editing:"):
        # Extract the username
        old_bot_username = current_state.split(":")[1]
        new_url = message.text.strip()

        # Validate URL
        url_pattern = re.compile(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!$&'()*+,;=.]+$" # Corrected Regex
        )
        if not url_pattern.match(new_url):
            await message.reply_text("❌ **Invalid URL format.**")
            return

        # Ensure URL is HTTPS
        if new_url.startswith("http://"):
            new_url = new_url.replace("http://", "https://")
        elif not new_url.startswith("https://"):
            new_url = "https://" + new_url
        # Reload settings

        settings = load_settings()
        # Update the redirect URL
        for pair in settings["username_redirect_pairs"]:
            if pair["username"] == old_bot_username:
                pair["redirect_url"] = new_url
                save_settings(settings)
                await message.reply_text(f"✅ **Redirect URL for `{old_bot_username}` updated to:** `{new_url}`")
                user_states.pop(user_id, None)
                return  # Exit the function after updating

        # If we get here, the username wasn't found (shouldn't happen if state is managed correctly)
        await message.reply_text(f"❌ **Error: Username `{old_bot_username}` not found (unexpected).**")
        user_states.pop(user_id, None)  # Clear the state to prevent getting stuck

    else:
        # Ignore if not in the correct state.
        return

# =========================== View Config ===========================
@bot.on_message(filters.command("config"))
async def view_config(client: Client, message: Message):
    config_text = "⚙ **Current Bot Configuration:**\n\n"
    if settings["username_redirect_pairs"]:
        for pair in settings["username_redirect_pairs"]:
            config_text += f"🔹 **Username:** `{pair['username']}`, **Redirect URL:** `{pair['redirect_url']}`\n"
    else:
        config_text += "No usernames/redirect URLs configured yet."

    await message.reply_text(config_text, disable_web_page_preview=True)

# =========================== Handle Button Clicks ===========================
@bot.on_callback_query()
async def button_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "config":
      config_text = "⚙ **Current Bot Configuration:**\n\n"
      if settings["username_redirect_pairs"]:
          for pair in settings["username_redirect_pairs"]:
              config_text += f"🔹 **Username:** `{pair['username']}`, **Redirect URL:** `{pair['redirect_url']}`\n"
      else:
          config_text += "No usernames/redirect URLs configured yet."

      await query.message.edit_text(
          config_text,
            reply_markup=InlineKeyboardMarkup([
              [InlineKeyboardButton("➕ Add Old Bot Username", callback_data="add_old_bot_username")],
              [InlineKeyboardButton("🔗 Set Redirect URL", callback_data="set_redirect_url")],
              [InlineKeyboardButton("✏️ Edit Redirect URL", callback_data="edit_redirect_url")],
              [InlineKeyboardButton("🗑️ Delete Username", callback_data="delete_old_bot_username")],
              [InlineKeyboardButton("🔙 Back", callback_data="help")]
          ]),
          disable_web_page_preview=True
      )
    elif data == "help":
        await help_command(client, query.message)
    elif data == "set_redirect_url":
        user_states[user_id] = "waiting_for_url"  #Set the user state
        await query.message.edit_text(
        "🔗 **Send the new redirect URL AND the associated old bot username, separated by a space.**\n\n"
        "Example: `http://secure.tg-files.com/skyking/bot8 HD10SHARE888888BOT`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]]))
    elif data == "add_old_bot_username":
        user_states[user_id] = "waiting_for_username" #Set the user state
        await query.message.edit_text(
        "🤖 **Send the username of the old bot you are adding** (e.g., `HD10SHARE888888BOT`).  **Do not include the @ symbol.**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
        )
    elif data == "edit_redirect_url":
        user_states[user_id] = "waiting_for_edit"
        await query.message.edit_text(
            "✏️ **Send the OLD BOT USERNAME whose redirect URL you want to edit.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
        )

    elif data == "delete_old_bot_username":
        user_states[user_id] = "waiting_for_delete"
        await query.message.edit_text(
            "🗑️ **Send the username of the old bot you want to DELETE.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="config")]])
        )

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
# End of part 2 of 4
# ====================== Handle Link Conversion ======================
@bot.on_message(filters.text & filters.user(ALLOWED_USERS) & ~filters.command(["start", "help", "config", "set_redirect_url", "add_old_bot_username", "edit_redirect_url", "delete_old_bot_username","stop_conversion"]))
async def handle_link_conversion(client: Client, message: Message):
    """Converts multiple links from the input message."""
    user_id = message.from_user.id
    if user_states.get(user_id) != "converting":
        return  # Only process if in converting state

    input_text = message.text.strip()
    output_lines = []

    # Reload settings from the database
    global settings
    settings = load_settings()

    # Check if there are ANY configured usernames/redirect URLs
    if not settings["username_redirect_pairs"]:
        await message.reply_text("❌ **No redirect URLs configured.** Please add a username and redirect URL using `/add_old_bot_username` and `/set_redirect_url`.")
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

            # Iterate through ALL configured username/redirect URL pairs
            username_matched = False
            for pair in settings["username_redirect_pairs"]:
                if extracted_username == pair["username"]:
                    new_url = f"{pair['redirect_url']}?start={start_parameter}"
                    new_url = new_url.replace("//?start", "/?start")
                    output_lines.append(f"[{text_part} + {new_url}]")
                    username_matched = True
                    break  # Important: Stop after the FIRST match

            if not username_matched:
                output_lines.append(line) #If no username matched in the settings, append original
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

#End of Part 3 of 3
