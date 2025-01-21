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
async def pm_broadcast(bot, message):
    BATCH_SIZE = 100  # Number of users processed in each batch
    SEMAPHORE_LIMIT = 60  # Maximum concurrent tasks
    BATCH_DELAY = 1  # Delay in seconds between batches

    # Ask for the broadcast message
    b_msg = await bot.ask(chat_id=message.from_user.id, text="Now Send Me Your Broadcast Message")

    try:
        users = await query_msg()  # Get all users
        sts = await message.reply_text("Broadcasting your messages...")
        start_time = time.time()

        total_users = len(users)
        done, blocked, deleted, failed, success = 0, 0, 0, 0, 0

        sem = asyncio.Semaphore(SEMAPHORE_LIMIT)

        async def send_message(user):
            nonlocal success, blocked, deleted, failed, done
            async with sem:
                user_id = int(user[0])  # Extract user ID from the query
                try:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=b_msg.chat.id,
                        message_id=b_msg.id
                    )
                    success += 1
                except FloodWait as e:
                    LOGGER.warning(f"FloodWait for {e.value} seconds. Pausing...")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    if "blocked" in str(e).lower():
                        blocked += 1
                    elif "deleted" in str(e).lower():
                        deleted += 1
                    else:
                        failed += 1
                    LOGGER.error(f"Failed to send to {user_id}: {e}")
                finally:
                    done += 1

        batch_tasks = []
        batch_count = 0

        for user in users:
            batch_tasks.append(send_message(user))
            batch_count += 1

            if batch_count >= BATCH_SIZE:
                await asyncio.gather(*batch_tasks)
                batch_tasks = []
                batch_count = 0

                # Live status update
                await sts.edit(
                    f"Broadcast in progress:\n\n"
                    f"Total Users: {total_users}\n"
                    f"Completed: {done}/{total_users}\n"
                    f"Success: {success}\n"
                    f"Blocked: {blocked}\n"
                    f"Deleted: {deleted}\n"
                    f"Failed: {failed}"
                )
                await asyncio.sleep(BATCH_DELAY)

        # Process any remaining users
        if batch_tasks:
            await asyncio.gather(*batch_tasks)

        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await sts.edit(
            f"Broadcast Completed:\n\n"
            f"Time Taken: {time_taken}\n"
            f"Total Users: {total_users}\n"
            f"Completed: {done}/{total_users}\n"
            f"Success: {success}\n"
            f"Blocked: {blocked}\n"
            f"Deleted: {deleted}\n"
            f"Failed: {failed}"
        )
    except Exception as e:
        LOGGER.error(f"Broadcasting error: {e}")
