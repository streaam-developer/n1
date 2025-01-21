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
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyrogram.types import ChatJoinRequest

from pyrogram.errors import UserNotParticipant, RPCError

async def is_subscribed(bot, message, channel_id):
    """
    Check if a user is subscribed to a public channel.
    """
    try:
        user_id = message.from_user.id
        member = await bot.get_chat_member(channel_id, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False
