from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

# Initialize Pyrogram Client
app = Client(
    "FilterBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Memory based filter database
filters_db = {}

# ✅ /start command + notify owner
@app.on_message(filters.command("start"))
async def start_command(client, message):
    mention = message.from_user.mention if message.from_user else "User"
    text = (
        f"👋 Hello {mention}!\n\n"
        f"I'm your **Filter Bot** 🤖\n"
        f"Use these commands:\n"
        f"/filter - add new filter\n"
        f"/filters - see all filters\n"
        f"/stop - delete filter"
    )
    await message.reply_text(text)

    # Notify owner privately
    try:
        await client.send_message(Config.OWNER_ID, "✅ Bot has started and is online!")
    except Exception:
        pass

# 🧩 /filter command to add new filters
@app.on_message(filters.command("filter"))
async def add_filter(client, message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this bot.")

    try:
        text = message.text.split(" ", 1)[1]
        parts = text.split(" ", 1)
        keyword = parts[0].lower()
        content = parts[1]

        # Parse buttons
        buttons = []
        if "[" in content and "]" in content:
            main_text = content.split("[")[0].strip()
            button_parts = content.split("[")[1:]
            row = []
            for bp in button_parts:
                bp = bp.replace("]", "")
                if "(buttonlink:" in bp and ")(buttontext:" in bp:
                    try:
                        link = bp.split("(buttonlink:")[1].split(")")[0]
                        text_btn = bp.split("(buttontext:")[1].split(")")[0]
                        row.append(InlineKeyboardButton(text=text_btn, url=link))
                        if "&&" not in bp:
                            buttons.append(row)
                            row = []
                    except Exception:
                        pass
            if row:
                buttons.append(row)
        else:
            main_text = content

        filters_db[keyword] = {
            "text": main_text,
            "buttons": InlineKeyboardMarkup(buttons) if buttons else None
        }

        await message.reply_text(f"✅ Filter added for **{keyword}**")

    except Exception as e:
        await message.reply_text(
            "⚠️ Format Error!\n\nExample:\n"
            "`/filter naruto Naruto Kai [buttonlink:https://link.com](buttontext:Watch Now)`"
        )

# 📋 /filters command to list all filters
@app.on_message(filters.command("filters"))
async def show_filters(client, message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this bot.")

    if not filters_db:
        return await message.reply_text("😕 No filters added yet.")
    flist = "\n".join([f"• {k}" for k in filters_db.keys()])
    await message.reply_text(f"📂 **Saved Filters:**\n\n{flist}")

# 🗑️ /stop command to delete filters
@app.on_message(filters.command("stop"))
async def stop_filter(client, message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this bot.")
    try:
        keyword = message.text.split(" ", 1)[1].lower()
        if keyword in filters_db:
            del filters_db[keyword]
            await message.reply_text(f"🗑️ Filter '{keyword}' deleted.")
        else:
            await message.reply_text("❌ Filter not found.")
    except:
        await message.reply_text("⚠️ Usage: /stop <keyword>")

# 💬 Auto reply in Target Chat
@app.on_message(filters.text & filters.chat(Config.TARGET_CHAT_ID))
async def auto_reply(client, message):
    text = message.text.lower()
    for keyword, data in filters_db.items():
        if keyword in text:
            await message.reply_text(
                data["text"],
                reply_markup=data["buttons"] if data["buttons"] else None
            )
            break

# 🟢 Run Bot
if __name__ == "__main__":
    print("✅ Filter Bot Started Successfully!")
    app.run()
