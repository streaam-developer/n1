import os
import sys
import asyncio
import time
import shutil
from psutil import cpu_percent, virtual_memory, disk_usage
from pyrogram import Client, filters
from mfinder.db.broadcast_sql import add_user
from mfinder.db.settings_sql import get_search_settings, change_search_settings
from mfinder.utils.constants import STARTMSG, HELPMSG
from mfinder import *
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    LinkPreviewOptions,
)
from mfinder.utils.util_support import *
from mfinder.plugins.serve import get_files
from mfinder.db.token_sql import *



@Client.on_message(filters.command(["start"]))
async def start(bot, update):
    client = bot
    message = update

    # Handle cases where no arguments are passed to /start
    if len(message.command) < 2:
        await message.reply_text("Welcome! Use the bot commands to get started.")
        return

    data = message.command[1]

    # Handle "verify" token logic
    if data.split("-", 1)[0] == "verify":
        try:
            userid = data.split("-", 2)[1]
            token = data.split("-", 3)[2]

            if str(message.from_user.id) != str(userid):
                return await message.reply_text(
                    text="<b>Invalid link or Expired link!</b>",
                    protect_content=True,
                )

            # Validate the token
            is_valid = await check_token(userid, token)
            if is_valid:
                await message.reply_text(
                    text=f"<b>Hey {message.from_user.mention}, You are successfully verified!</b>",
                    protect_content=True,
                )
                await verify_user(userid, token)
            else:
                return await message.reply_text(
                    text="<b>Invalid link or Expired link!</b>",
                    protect_content=True,
                )
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
            return

    # Register new user
    if len(message.command) == 1:
        user_id = message.from_user.id
        name = message.from_user.first_name or " "
        user_name = f"@{message.from_user.username}" if message.from_user.username else None

        try:
            await add_user(user_id, user_name)
        except Exception as e:
            print(f"Error adding user: {e}")

        # Prepare the start message
        try:
            start_msg = START_MSG.format(name, user_id)
        except Exception as e:
            print(f"Error formatting start message: {e}")
            start_msg = "Welcome to the bot!"

        # Check if verification is required
        if not await check_verification(client, user_id) and VERIFY is True:
            try:
                verify_link = await get_token(client, user_id, f"https://telegram.me/{BOT_USERNAME}?start=")
                btn = [
                    [InlineKeyboardButton("Verify", url=verify_link)],
                    [InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)],
                ]
                await message.reply_text(
                    text="<b>You are not verified!\nKindly verify to continue!</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn),
                )
            except Exception as e:
                print(f"Error generating verification link: {e}")
                await message.reply_text("Unable to generate verification link. Please try again.")
            return

        # Send the welcome message
        await bot.send_message(
            chat_id=message.chat.id,
            text=start_msg,
            reply_to_message_id=message.reply_to_message_id,
            reply_markup=START_KB,
        )

        # Update search settings
        try:
            search_settings = await get_search_settings(user_id)
            if not search_settings:
                await change_search_settings(user_id, link_mode=True)
        except Exception as e:
            print(f"Error updating search settings: {e}")

    # Handle /start with additional data
    elif len(message.command) == 2:
        try:
            await get_files(bot, message)
        except Exception as e:
            print(f"Error processing get_files: {e}")

@Client.on_message(filters.command(["help"]) & filters.user(ADMINS))
async def help_m(bot, update):
    try:
        help_msg = HELP_MSG
    except Exception as e:
        LOGGER.warning(e)
        help_msg = HELPMSG

    await bot.send_message(
        chat_id=update.chat.id,
        text=help_msg,
        reply_to_message_id=update.reply_to_message_id,
        reply_markup=HELP_KB,
    )


@Client.on_callback_query(filters.regex(r"^back_m$"))
async def back(bot, query):
    user_id = query.from_user.id
    name = query.from_user.first_name if query.from_user.first_name else " "
    try:
        start_msg = START_MSG.format(name, user_id)
    except Exception as e:
        LOGGER.warning(e)
        start_msg = STARTMSG
    await query.message.edit_text(start_msg, reply_markup=START_KB)


@Client.on_callback_query(filters.regex(r"^help_cb$"))
async def help_cb(bot, query):
    try:
        help_msg = HELP_MSG
    except Exception as e:
        LOGGER.warning(e)
        help_msg = HELPMSG
    await query.message.edit_text(help_msg, reply_markup=HELP_KB)


@Client.on_message(filters.command(["restart"]) & filters.user(ADMINS))
async def restart(bot, update):
    LOGGER.warning("Restarting bot using /restart command")
    msg = await update.reply_text(text="__Restarting.....__")
    await asyncio.sleep(5)
    await msg.edit("__Bot restarted !__")
    os.execv(sys.executable, ["python3", "-m", "mfinder"] + sys.argv)


@Client.on_message(filters.command(["logs"]) & filters.user(ADMINS))
async def log_file(bot, update):
    logs_msg = await update.reply("__Sending logs, please wait...__")
    try:
        await update.reply_document("logs.txt")
    except Exception as e:
        await update.reply(str(e))
    await logs_msg.delete()


@Client.on_message(filters.command(["server"]) & filters.user(ADMINS))
async def server_stats(bot, update):
    sts = await update.reply_text("__Calculating, please wait...__")
    total, used, free = shutil.disk_usage(".")
    ram = virtual_memory()
    start_t = time.time()
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000

    ping = f"{time_taken_s:.3f} ms"
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    t_ram = humanbytes(ram.total)
    u_ram = humanbytes(ram.used)
    f_ram = humanbytes(ram.available)
    cpu_usage = cpu_percent()
    ram_usage = virtual_memory().percent
    used_disk = disk_usage("/").percent
    db_size = get_db_size()

    stats_msg = f"--**BOT STATS**--\n`Ping: {ping}`\n\n--**SERVER DETAILS**--\n`Disk Total/Used/Free: {total}/{used}/{free}\nDisk usage: {used_disk}%\nRAM Total/Used/Free: {t_ram}/{u_ram}/{f_ram}\nRAM Usage: {ram_usage}%\nCPU Usage: {cpu_usage}%`\n\n--**DATABASE DETAILS**--\n`Size: {db_size} MB`"
    try:
        await sts.edit(stats_msg)
    except Exception as e:
        await update.reply_text(str(e))
