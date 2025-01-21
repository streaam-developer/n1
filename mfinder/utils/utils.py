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

async def is_subscribed(bot, query, channel_id, invite_link):
    """
    Check if a user is subscribed to the given channel.
    If not subscribed, send the invite link.
    """
    invite_link = AUTH_LINK
    try:
        # Check if the user is a member of the channel
        user = await bot.get_chat_member(channel_id, query.from_user.id)
        if user.status in ["member", "administrator", "creator"]:
            return True  # User is subscribed
    except UserNotParticipant:
        # User is not a participant, send the invite link
        await query.message.reply_text(
            f"Please join this channel to continue: [Join Here]({invite_link})",
            disable_web_page_preview=True,
        )
        return False
    except Exception as e:
        # Handle any other exceptions
        print(f"Error checking subscription: {e}")
        return False
