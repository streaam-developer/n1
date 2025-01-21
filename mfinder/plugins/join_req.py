from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from mfinder.db.broadcast_sql import check_join_request, add_join_request, delete_all_join_requests
from mfinder import ADMINS, SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL, AUTH_LINK

from mfinder.utils.utils import *
FSUB_CHANNELS = [THIRD_AUTH_CHANNEL]

# Updated join_req.py with improved join request handling
from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, RPCError
from mfinder.utils.utils import temp
from mfinder import FSUB_CHANNELS, AUTH_LINK

# Check if a user is subscribed to a channel or pending approval
async def check_subscription(bot, user_id, chat_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except UserNotParticipant:
        return await is_pending_approval(bot, user_id, chat_id)
    return False

# Check if the user is in the pending approval list
async def is_pending_approval(bot, user_id, chat_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == "restricted" and not member.is_member:
            return True
    except RPCError as e:
        print(f"Error checking pending approval: {e}")
    return False

# Fetch pending join requests for a channel
async def search_pending_requests(bot, chat_id, user_id=None):
    try:
        requests = await bot.get_chat_join_requests(chat_id)
        if user_id:
            for req in requests:
                if req.from_user.id == user_id:
                    return req
            return None
        return requests
    except Exception as e:
        print(f"Error fetching join requests: {e}")
        return []

@Client.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client: Client, request: ChatJoinRequest):
    user = request.from_user
    chat_id = request.chat.id

    # Check subscription or pending approval
    subscribed = await check_subscription(client, user.id, chat_id)
    if subscribed:
        try:
            # Approve the join request
            await client.approve_chat_join_request(chat_id, user.id)
            print(f"Approved join request for user: {user.id}")
        except ChatAdminRequired:
            print(f"Bot must be admin in channel {chat_id} to approve requests.")
        except Exception as e:
            print(f"Error approving join request: {e}")
    else:
        print(f"User {user.id} is not subscribed or pending approval.")

@Client.on_message(filters.command("check_request") & filters.private)
async def check_request_status(client: Client, message: Message):
    chat_id = -1001234567890  # Replace with your channel ID
    user_id = message.from_user.id

    # Check if user is subscribed
    subscribed = await check_subscription(client, user_id, chat_id)
    if subscribed:
        await message.reply_text("You are already a member!")
    else:
        # Check if user is in pending requests
        pending_request = await search_pending_requests(client, chat_id, user_id=user_id)
        if pending_request:
            await message.reply_text("You are in the pending approval list.")
        else:
            await message.reply_text("You are not a member or pending approval.")

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    # Delete all join requests from the database
    await delete_all_join_requests()
    await message.reply("ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ")
