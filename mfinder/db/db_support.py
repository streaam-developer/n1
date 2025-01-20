import asyncio
from pyrogram.errors import FloodWait
from pyrogram import enums
from mfinder import LOGGER
from mfinder.db.broadcast_sql import query_msg, del_user

from mfinder.db.broadcast_sql import count_users  # Import count_users

from sqlalchemy import create_engine, Column, String, Integer, Boolean, BigInteger, Numeric

async def users_info(bot):
    total_users = await count_users()
    # Blocked users ka count (optional, implement if needed)
    blocked_users = 0
    return total_users, blocked_users