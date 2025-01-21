import os
import sys, random,string
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



from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from mfinder.utils.utils import *


@Client.on_message(filters.command(["start"], prefixes="/"))
async def start(bot, update: Message):
    user_id = update.from_user.id
    name = update.from_user.first_name or "User"
    user_name = "@" + update.from_user.username if update.from_user.username else None

    # Add user to the database if not already present
    await add_user(user_id, user_name)

    IS_VERIFY = False  # Set this to True if verification is needed

    # Check if user started with a parameter
    start_params = update.text.split(" ", 1)  # Split command and its arguments
    if len(start_params) == 1:
        # No parameters, send a basic welcome message
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"Hello {name}, welcome to the bot!",
            reply_markup=START_KB,
        )
        return

    # Only proceed with verification logic if IS_VERIFY is True
    if IS_VERIFY:
        # Extract parameter
        param = start_params[1]

        # Handle verification parameter
        if param.startswith("verify_"):
            token = param.split("verify_")[1]
            verify_status = await get_verify_status(user_id)

            if verify_status and verify_status['verify_token'] == token:
                # Mark user as verified
                await update_verify_status(user_id, is_verified=True, verify_token=None)

                # Send success message and requested file
                await bot.send_message(
                    chat_id=update.chat.id,
                    text=f"Thank you {name}, you are now verified! Here is your file:",
                )
                await get_files(bot, update)
            else:
                # Invalid or expired token
                await bot.send_message(
                    chat_id=update.chat.id,
                    text="Invalid or expired verification link. Please restart to generate a new one.",
                )
            return

        # For users starting without verification
        verify_status = await get_verify_status(user_id)

        if not verify_status or not verify_status['is_verified']:
            # Generate new verification token
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            # Update database with new token (replace old one if exists)
            await update_verify_status(user_id, verify_token=token, is_verified=False)

            # Create verification link
            bot_username = BOTUSERNAME
            verification_link = await get_shortlink(
                SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{bot_username}?start=verify_{token}'
            )

            # Send verification instructions
            await bot.send_message(
                chat_id=update.chat.id,
                text="To access the bot, please verify yourself using the link below:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Click here to verify", url=verification_link)],
                    [InlineKeyboardButton("How to use the bot", url=TUT_VID)]
                ]),
            )
            return

        # Verified users
        if verify_status['is_verified']:
            await bot.send_message(
                chat_id=update.chat.id,
                text=f"Welcome back, {name}! Here is your file:",
            )
            await get_files(bot, update)
    else:
        # If IS_VERIFY is False, skip verification and provide the file directly
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"Hello {name}, welcome to the bot! Here is your file:",
        )
        await get_files(bot, update)

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
