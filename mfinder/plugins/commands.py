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


@Client.on_message(filters.command(["start"]))
async def start(bot, update: Message):
    client = bot
    user_id = update.from_user.id
    name = update.from_user.first_name if update.from_user.first_name else " "
    user_name = (
        "@" + update.from_user.username if update.from_user.username else None
    )
    
    # Add user logic (can be your own function or DB update)
    await add_user(user_id, user_name)

    # Check the verification status of the user
    verify_status = await get_verify_status(user_id)
    
    # Check if the user is coming for the first time and send a normal start message
    if not verify_status:
        start_msg = START_MSG.format(name, user_id)
        await bot.send_message(
            chat_id=update.chat.id,
            text=start_msg,
            reply_to_message_id=update.reply_to_message_id,
            reply_markup=START_KB,
        )
        return  # Stop further processing for new users

    # Handle expired verification
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(user_id, is_verified=False)

    # Token verification process
    if "verify_" in update.text:
        _, token = update.text.split("_", 1)
        
        # Check if token matches
        if verify_status['verify_token'] != token:
            return await bot.send_message(
                chat_id=update.chat.id,
                text="Your token is invalid or expired. Try again by clicking /start"
            )

        # If valid token, update verification status
        await update_verify_status(user_id, is_verified=True, verified_time=time.time())
        reply_markup = None if verify_status["link"] == "" else None
        await bot.send_message(
            chat_id=update.chat.id,
            text="Your token has been successfully verified and is valid for: 24 Hours",
            reply_markup=reply_markup,
            protect_content=False
        )

    elif verify_status['is_verified']:
        # If user is verified, send a welcome message and provide files
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("About Me", callback_data="about"),
              InlineKeyboardButton("Close", callback_data="close")]]
        )
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"Welcome {update.from_user.first_name}!\n\nID: {update.from_user.id}",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        # Logic to automatically provide files if verified can be added here
        await get_files(bot, update)  # Assuming get_files is your function to provide files

    else:
        # If user is not verified, provide a verification link
        if IS_VERIFY and not verify_status['is_verified']:
            bot.username = BOTUSERNAME
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Remove old verification token and update the new one
            await update_verify_status(user_id, verify_token=token, link="")

            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{bot.username}?start=verify_{token}')
            btn = [
                [InlineKeyboardButton("Click here to verify", url=link)],
                [InlineKeyboardButton('How to use the bot', url=TUT_VID)]
            ]
            await bot.send_message(
                chat_id=update.chat.id,
                text=f"Your Ads token is expired. Refresh your token and try again.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. Once you pass an ad, you can use the bot for 24 hours.",
                reply_markup=InlineKeyboardMarkup(btn),
                protect_content=False
            )

    # Ensure search settings for the user
    search_settings = await get_search_settings(user_id)
    if not search_settings:
        await change_search_settings(user_id, link_mode=True)

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
