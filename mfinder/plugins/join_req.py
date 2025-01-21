from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from mfinder.db.broadcast_sql import check_join_request, add_join_request, delete_all_join_requests
from mfinder import ADMINS, SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL
from utils.utils import temp, is_subscribed

FSUB_CHANNELS = [SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL]

@Client.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client: Client, message: ChatJoinRequest):
    user = message.from_user

    # Check if the join request exists in the database
    if not await check_join_request(user.id, message.chat.id):
        await add_join_request(user.id, message.chat.id)  # Add join request to the database

    # Verify if the user is subscribed to all required channels
    all_joined = True
    for channel_id in FSUB_CHANNELS:
        if not await is_subscribed(client, message, [channel_id]):
            all_joined = False
            break

    # If subscribed to all channels, handle the delete action
    if all_joined:
        dl = temp.DEL_MSG.get(user.id)
        if dl:
            await dl.delete()

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    # Delete all join requests from the database
    await delete_all_join_requests()
    await message.reply("ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ")
