import asyncio
import time
import datetime
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from mfinder import LOGGER
from mfinder.db.db_support import users_info
from mfinder.db.broadcast_sql import query_msg
from mfinder import ADMINS, OWNER_ID


@Client.on_message(
    filters.private & filters.command("stats") & filters.user(ADMINS)
)
async def get_subscribers_count(bot: Client, message: Message):
    """Command to display total subscriber stats."""
    wait_msg = "__Calculating, please wait...__"
    msg = await message.reply_text(wait_msg)
    
    # Fetch total user count
    total_users = await users_info(bot)
    stats_msg = f"**Stats**\nTotal Subscribers: `{total_users}`"
    await msg.edit(stats_msg)


@Client.on_message(
    filters.private & filters.command("broadcast") & filters.user(ADMINS)
)
async def send_text(bot, message: Message):
    """Command to broadcast a message to all subscribers."""
    if "broadcast" in message.text and message.reply_to_message is not None:
        start_time = time.time()
        progress_msg = await message.reply_text("Broadcasting started...")
        
        # Fetch all user IDs
        query = await query_msg()
        if not query:
            await progress_msg.edit_text("No users found in the database!")
            LOGGER.error("Broadcast aborted: No users found in the database!")
            return

        LOGGER.info(f"Users fetched from DB: {len(query)}")
        
        success = 0
        failed = 0
        
        for row in query:
            chat_id = int(row[0])  # Fetch user ID
            try:
                # Send message to user
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.reply_to_message_id,
                    reply_markup=message.reply_to_message.reply_markup,
                )
                success += 1
                LOGGER.info(f"Broadcast sent to {chat_id}")
            except FloodWait as e:
                LOGGER.warning(f"FloodWait for {e.value} seconds. Pausing...")
                await asyncio.sleep(e.value)
            except Exception as e:
                LOGGER.error(f"Failed to send to {chat_id}: {e}")
                failed += 1
            
            # Optional: Update live stats
            await progress_msg.edit_text(
                f"**Broadcasting...**\nSent: `{success}`\nFailed: `{failed}`\nRemaining: `{len(query) - (success + failed)}`"
            )
        
        # Calculate time taken
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await progress_msg.edit_text(
            f"**Broadcast Completed**\nSent to: `{success}`\nBlocked / Deleted: `{failed}`\nCompleted in `{time_taken}` HH:MM:SS"
        )
    else:
        reply_error = "`Use this command as a reply to any telegram message.`"
        msg = await message.reply_text(reply_error)
        await asyncio.sleep(8)
        await msg.delete()
