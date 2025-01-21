# temp db for banned 
class temp(object):
   DEL_MSG = {}



import logging
from pyrogram.errors import UserNotParticipant
from db.broadcast_sql import check_join_request

# Initialize logger
logger = logging.getLogger(__name__)

async def is_subscribed(bot, query, FSUB_CHANNELS):
    """
    Check if a user is subscribed to all channels listed in FSUB_CHANNELS.

    Args:
        bot: The Pyrogram bot instance.
        query: The callback query or message containing the user information.
        FSUB_CHANNELS (list): List of channel IDs to check for subscription.

    Returns:
        bool: True if the user is subscribed to all channels, False otherwise.
    """
    try:
        for channel in FSUB_CHANNELS:  # Iterate over each channel
            # Check if there is a join request in the current channel
            join_request_exists = await check_join_request(query.from_user.id, int(channel))

            if join_request_exists:
                continue  # If join request exists, move to the next channel

            try:
                # Check if the user is a member of the current channel
                user = await bot.get_chat_member(int(channel), query.from_user.id)
            except UserNotParticipant:
                return False  # If the user is not a participant in any one channel, return False
            except Exception as e:
                logger.exception(f"Error checking membership for channel {channel}: {e}")
                return False  # Return False if any other error occurs

            # If the user is banned ('kicked'), return False
            if user.status == 'kicked':
                return False

    except Exception as e:
        logger.exception(f"Unexpected error in is_subscribed: {e}")
        return False  # In case of any other error, return False

    return True  # If the user is subscribed to all channels, return True