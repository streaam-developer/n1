from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from mfinder.db.broadcast_sql import check_join_request, add_join_request, delete_all_join_requests
from mfinder import ADMINS, SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL, AUTH_LINK

from mfinder.utils.utils import *
FSUB_CHANNELS = [SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL]

@Client.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client: Client, message: ChatJoinRequest):
    user = message.from_user
    all_joined = True

    # Use the permanent invite link for all required channels
    for channel_id in FSUB_CHANNELS:
        if not await is_subscribed(client, message, channel_id, AUTH_LINK):
            all_joined = False
            break

    # If the user is subscribed to all channels, approve the request
    if all_joined:
        await client.approve_chat_join_request(chat_id=message.chat.id, user_id=user.id)

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    # Delete all join requests from the database
    await delete_all_join_requests()
    await message.reply("ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ")
