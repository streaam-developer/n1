
from mfinder.db.token_sql import *
import aiohttp
from shortzy import Shortzy
from datetime import timedelta

async def get_verify_status(user_id):
    """
    Fetch the verification status of a user from the database.
    Args:
        user_id (int): The user's ID.
    Returns:
        dict: Verification status details (is_verified, verified_time, token, etc.).
    """
    return await db_verify_status(user_id)

async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link=""):
    """
    Update the verification details of a user in the database.
    Args:
        user_id (int): The user's ID.
        verify_token (str): The new verification token.
        is_verified (bool): The verification status.
        verified_time (int): The timestamp until which the user is verified.
        link (str): The verification link.
    """
    current = await db_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    await db_update_verify_status(user_id, current)

async def get_shortlink(url, api, link):
    """
    Shorten a given URL using the Shortzy API.
    Args:
        url (str): The base URL for Shortzy.
        api (str): The API key for Shortzy.
        link (str): The original long link to be shortened.
    Returns:
        str: The shortened link or an error message if shortening fails.
    """
    shortzy = Shortzy(api_key=api, base_site=url)
    try:
        return await shortzy.convert(link)
    except Exception as e:
        return f"Error shortening link: {str(e)}"

def get_exp_time(seconds):
    """
    Convert a duration in seconds into a readable string format.
    Args:
        seconds (int): Duration in seconds.
    Returns:
        str: Readable format like '1days2hours30mins'.
    """
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    return ''.join(f"{seconds // period_seconds}{period_name}" if (seconds := seconds % period_seconds) else ''
                   for period_name, period_seconds in periods)

def get_readable_time(seconds: int) -> str:
    """
    Convert seconds into a readable time format (e.g., '2d:5h:30m').
    Args:
        seconds (int): Time in seconds.
    Returns:
        str: Readable time format.
    """
    td = timedelta(seconds=seconds)
    days, seconds = divmod(td.total_seconds(), 86400)
    return f"{int(days)}d:{str(td)}".split(",")[1].strip() if days else str(td)

