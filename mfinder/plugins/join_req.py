from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from mfinder.db.broadcast_sql import check_join_request, add_join_request, delete_all_join_requests
from mfinder import ADMINS, SECOND_AUTH_CHANNEL, THIRD_AUTH_CHANNEL, AUTH_LINK

from mfinder.utils.utils import *
FSUB_CHANNELS = [THIRD_AUTH_CHANNEL]

from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyrogram.errors import UserNotParticipant, ChatAdminRequired

async def is_subscribed(bot, query, channel_id, invite_link):
    """
    Check if a user is subscribed to a private channel or group.
    """
    try:
        # Check if the user is a member of the channel
        user = await bot.get_chat_member(channel_id, query.from_user.id)
        if user.status in ["member", "administrator", "creator"]:
            return True
    except UserNotParticipant:
        # User is not subscribed
        await query.reply_text(  # Use query.reply_text instead of query.message.reply_text
            f"Please join the private channel using this link: [Join Here]({invite_link})",
            disable_web_page_preview=True,
        )
        return False
    except ChatAdminRequired:
        # Bot lacks admin privileges
        logger.error(f"Bot must be an admin in channel: {channel_id}")
        raise
    except Exception as e:
        # Log other exceptions
        logger.error(f"Error checking subscription for channel {channel_id}: {e}")
        raise

    return False


@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    # Delete all join requests from the database
    await delete_all_join_requests()
    await message.reply("ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ")
