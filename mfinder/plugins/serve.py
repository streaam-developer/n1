import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    LinkPreviewOptions,
)
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from mfinder.db.files_sql import (
    get_filter_results,
    get_file_details,
    get_precise_filter_results,
)
import pytz, traceback, requests, string, tracemalloc, logging, random, math, ast, os, re, asyncio
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
from mfinder.db.settings_sql import (
    get_search_settings,
    get_admin_settings,
    get_link,
    get_channel,
)
from mfinder.db.ban_sql import is_banned
from mfinder.db.filters_sql import is_filter
from mfinder import LOGGER
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatJoinRequest
from pyrogram import Client, filters, enums
from .join_req import FSUB_CHANNELS
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from mfinder.db.settings_sql import get_channel, get_link
from mfinder.db.ban_sql import is_banned
from mfinder.db.filters_sql import is_filter
from mfinder import LOGGER
from pyrogram import Client, filters, enums
from mfinder import *
from mfinder.utils.utils import temp, is_subscribed
# Handle private messages
@Client.on_message(~filters.regex(r"^/") & filters.text & filters.private & filters.incoming)
async def filter_(bot, message):
    user_id = message.from_user.id

    # Skip commands or special characters
    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return

    # Check if user is banned
    if await is_banned(user_id):
        await message.reply_text("You are banned. You can't use this bot.", quote=True)
        return

    # Check subscription
    unjoined_channels = []
    for channel_id in FSUB_CHANNELS:
        if not await is_subscribed(bot, message, channel_id, AUTH_LINK):
            unjoined_channels.append(channel_id)

    if unjoined_channels:
        btn = [[InlineKeyboardButton("Join Channel", url=AUTH_LINK)]]
        btn.append([InlineKeyboardButton("I'm Subscribed ✅", callback_data="check_subscription")])
        subscribe_message = await message.reply_text(
            "Please join all required channels to use this bot.",
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
        )
        temp.DEL_MSG[user_id] = subscribe_message
        return

    # Check for filters
    fltr = await is_filter(message.text)
    if fltr:
        await message.reply_text(text=fltr.message, quote=True)
        return

    # Proceed with search
    if 2 < len(message.text) < 100:
        search = message.text
        page_no = 1
        me = bot.me
        username = me.username
        result, btn = await get_result(search, page_no, user_id, username)

        if result:
            await message.reply_text(result, reply_markup=InlineKeyboardMarkup(btn) if btn else None, quote=True)
        else:
            await message.reply_text("No results found. Try again with a different query.", quote=True)


# Handle group messages
@Client.on_message(filters.group & ~filters.regex(r"^/") & filters.text & filters.incoming)
async def group_filter_(bot, message):
    user_id = message.from_user.id
    group_id = message.chat.id

    # Skip commands or special characters
    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return

    # Check if user is banned
    if await is_banned(user_id):
        await message.reply_text("You are banned from using this bot.", quote=True)
        return

    # Check subscription
    unjoined_channels = []
    for channel_id in FSUB_CHANNELS:
        if not await is_subscribed(bot, message, channel_id, AUTH_LINK):
            unjoined_channels.append(channel_id)

    if unjoined_channels and ASKFSUBINGRP:
        btn = [[InlineKeyboardButton("Join Channel", url=AUTH_LINK)]]
        btn.append([InlineKeyboardButton("I'm Subscribed ✅", callback_data="groupchecksub")])
        subscribe_message = await message.reply_text(
            f"Hey {message.from_user.mention}, please join all required channels to request in the group.",
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
        )
        temp.DEL_MSG[user_id] = subscribe_message
        return

    # Check for filters
    fltr = await is_filter(message.text)
    if fltr:
        await message.reply_text(text=fltr.message, quote=True)
        return

    # Proceed with searching after joining the channel
    if 2 < len(message.text) < 100:
        search = message.text
        page_no = 1
        me = bot.me
        username = me.username
        result, btn = await get_result(search, page_no, user_id, username)

        if result:
            if btn:
                await message.reply_text(
                    f"{result}",
                    reply_markup=InlineKeyboardMarkup(btn),
                    quote=True,
                )
            else:
                await message.reply_text(
                    f"{result}",
                    quote=True,
                )
        else:
            await message.reply_text(
                text="No results found.\nOr retry with the correct spelling 🤐",
                quote=True,
            )




# Update the callback query handler to handle file requests in group and send to PM
from pyrogram.errors import PeerIdInvalid

@Client.on_callback_query(filters.regex(r"^file (.+)$"))
async def send_file_to_pm(bot, query):
    user_id = query.from_user.id
    file_id = query.data.split()[1]

    try:
        # Check if user has started the bot
        user = await bot.get_users(user_id)
        if user.is_bot:
            raise PeerIdInvalid  # Simulate an error if the user hasn't started the bot

        # Check if the callback is from the original user
        if query.from_user.id != user_id:
            await query.answer("Not allowed", show_alert=True)
            return

        # Inform the user that the file will be sent to their PM
        await query.answer("The file will be sent to your PM!", show_alert=True)

        # Retrieve file details
        filedetails = await get_file_details(file_id)
        admin_settings = await get_admin_settings()

        for files in filedetails:
            f_caption = files.caption or f"{files.file_name}"
            if admin_settings.custom_caption:
                f_caption = admin_settings.custom_caption

            f_caption = "`" + f_caption + "`"

            if admin_settings.caption_uname:
                f_caption += "\n" + admin_settings.caption_uname

            # Send file to user's PM
            await bot.send_cached_media(
                chat_id=user_id,
                file_id=file_id,
                caption=f_caption,
                parse_mode=ParseMode.MARKDOWN,
            )

            # Notify the user in the group chat that the file has been sent to their PM
            await query.message.reply_text(
                f"**The file '{files.file_name}' has been sent to your PM!**",
                quote=True,
            )

    except PeerIdInvalid:
        # If user hasn't started the bot, prompt them to do so
        await query.message.reply_text(
            "**Please start the bot in PM to receive the file!**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Start Bot", url=f"t.me/{bot.username}?start=start")]]
            ),
            quote=True,
        )

    except Exception as e:
        LOGGER.error(f"Error sending file to PM: {e}")

@Client.on_callback_query(filters.regex(r"^(nxt_pg|prev_pg) \d+ \d+ .+$"))
async def pages(bot, query):
    user_id = query.from_user.id
    org_user_id, page_no, search = query.data.split(maxsplit=3)[1:]
    org_user_id = int(org_user_id)
    page_no = int(page_no)
    me = bot.me
    username = me.username

    result, btn = await get_result(search, page_no, user_id, username)

    if result:
        try:
            if btn:
                await query.message.edit(
                    f"{result}",
                    reply_markup=InlineKeyboardMarkup(btn),
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
            else:
                await query.message.edit(
                    f"{result}",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
        except MessageNotModified:
            pass
    else:
        await query.message.reply_text(
            text="No results found.\nOr retry with the correct spelling 🤐",
            quote=True,
        )


async def get_result(search, page_no, user_id, username):
    search_settings = await get_search_settings(user_id)
    if search_settings:
        if search_settings.precise_mode:
            files, count = await get_precise_filter_results(query=search, page=page_no)
            precise_search = "Enabled"
        else:
            files, count = await get_filter_results(query=search, page=page_no)
            precise_search = "Disabled"
    else:
        files, count = await get_filter_results(query=search, page=page_no)
        precise_search = "Disabled"

    if search_settings:
        if search_settings.button_mode:
            button_mode = "ON"
        else:
            button_mode = "OFF"
    else:
        button_mode = "OFF"

    if search_settings:
        if search_settings.link_mode:
            link_mode = "ON"
        else:
            link_mode = "OFF"
    else:
        link_mode = "OFF"

    if button_mode == "ON" and link_mode == "OFF":
        search_md = "Button"
    elif button_mode == "OFF" and link_mode == "ON":
        search_md = "HyperLink"
    else:
        search_md = "List Button"

    if files:
        btn = []
        index = (page_no - 1) * 10
        crnt_pg = index // 10 + 1
        tot_pg = (count + 10 - 1) // 10
        btn_count = 0
        result = f"**Search Query:** `{search}`\n**Total Results:** `{count}`\n**Page:** `{crnt_pg}/{tot_pg}`\n**Precise Search: **`{precise_search}`\n**Result Mode:** `{search_md}`\n"
        page = page_no
        for file in files:
            if button_mode == "ON":
                file_id = file.file_id
                filename = f"[{get_size(file.file_size)}]{file.file_name}"
                btn_kb = InlineKeyboardButton(
                    text=f"{filename}", callback_data=f"file {file_id}"
                )
                btn.append([btn_kb])
            elif link_mode == "ON":
                index += 1
                btn_count += 1
                file_id = file.file_id
                filename = f"**{index}.** [{file.file_name}](https://t.me/{username}/?start={file_id}) - `[{get_size(file.file_size)}]`"
                result += "\n" + filename
            else:
                index += 1
                btn_count += 1
                file_id = file.file_id
                filename = (
                    f"**{index}.** `{file.file_name}` - `[{get_size(file.file_size)}]`"
                )
                result += "\n" + filename

                btn_kb = InlineKeyboardButton(
                    text=f"{index}", callback_data=f"file {file_id}"
                )

                if btn_count == 1 or btn_count == 6:
                    btn.append([btn_kb])
                elif 6 > btn_count > 1:
                    btn[0].append(btn_kb)
                else:
                    btn[1].append(btn_kb)

        nxt_kb = InlineKeyboardButton(
            text="Next >>",
            callback_data=f"nxt_pg {user_id} {page + 1} {search}",
        )
        prev_kb = InlineKeyboardButton(
            text="<< Previous",
            callback_data=f"prev_pg {user_id} {page - 1} {search}",
        )

        kb = []
        if crnt_pg == 1 and tot_pg > 1:
            kb = [nxt_kb]
        elif crnt_pg > 1 and crnt_pg < tot_pg:
            kb = [prev_kb, nxt_kb]
        elif tot_pg > 1:
            kb = [prev_kb]

        if kb:
            btn.append(kb)

        if button_mode and link_mode == "OFF":
            result = (
                result
                + "\n\n"
                + "🔻 __Tap on below corresponding file number to download.__ 🔻"
            )
        elif link_mode == "ON":
            result = result + "\n\n" + " __Tap on file name & then start to download.__"

        return result, btn

    return None, None


@Client.on_callback_query(filters.regex(r"^file (.+)$"))
async def get_files(bot, query):
    user_id = query.from_user.id
    if isinstance(query, CallbackQuery):
        file_id = query.data.split()[1]
        await query.answer("Sending file...", cache_time=60)
        cbq = True
    elif isinstance(query, Message):
        file_id = query.text.split()[1]
        cbq = False
    filedetails = await get_file_details(file_id)
    admin_settings = await get_admin_settings()
    for files in filedetails:
        f_caption = files.caption
        if admin_settings.custom_caption:
            f_caption = admin_settings.custom_caption
        elif f_caption is None:
            f_caption = f"{files.file_name}"

        f_caption = "`" + f_caption + "`"

        if admin_settings.caption_uname:
            f_caption = f_caption + "\n" + admin_settings.caption_uname

        if cbq:
            msg = await query.message.reply_cached_media(
                file_id=file_id,
                caption=f_caption,
                parse_mode=ParseMode.MARKDOWN,
                quote=True,
            )
        else:
            msg = await query.reply_cached_media(
                file_id=file_id,
                caption=f_caption,
                parse_mode=ParseMode.MARKDOWN,
                quote=True,
            )

        if admin_settings.auto_delete:
            delay_dur = admin_settings.auto_delete
            await asyncio.sleep(delay_dur)
            await msg.delete()

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return f"{size:.2f} {units[i]}"



