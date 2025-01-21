# temp db for banned 
class temp(object):
   DEL_MSG = {}



import logging
from pyrogram.errors import UserNotParticipant
from mfinder.db.broadcast_sql import check_join_request
from mfinder import *

# Initialize logger
logger = logging.getLogger(__name__)

from pyrogram.errors import UserNotParticipant
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
        await query.reply_text(  # Correctly use query.reply_text
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

