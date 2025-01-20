import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from mfinder import ADMINS, LOGGER
from mfinder.db.files_sql import save_file, delete_file
from mfinder.utils.helpers import edit_caption

# Global state management
lock = asyncio.Lock()
running_index_task = None
media_filter = filters.document | filters.video | filters.audio

@Client.on_message(filters.private & filters.user(ADMINS) & media_filter)
async def index_files(bot, message):
    user_id = message.from_user.id
    if lock.locked():
        await message.reply("Wait until the previous process is complete.")
        return

    try:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
        await bot.get_messages(chat_id, last_msg_id)

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Proceed", callback_data=f"index {chat_id} {last_msg_id}")],
                [InlineKeyboardButton("Cancel", callback_data="can-index")],
            ]
        )
        await bot.send_message(
            user_id, "Please confirm if you want to start indexing.", reply_markup=kb
        )
    except Exception as e:
        LOGGER.exception("Error starting indexing task")
        await message.reply_text(
            f"Unable to start indexing. Ensure the channel is public or the bot has admin access. Error: <code>{e}</code>"
        )

@Client.on_callback_query(filters.regex(r"^index -?\d+ \d+"))
async def index(bot, query):
    global running_index_task

    user_id = query.from_user.id
    chat_id, last_msg_id = map(int, query.data.split()[1:])

    if running_index_task:
        await query.message.reply("Another indexing task is already running.")
        return

    cancel_state = {"cancel": False}  # Track cancellation state
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Cancel", callback_data="cancel-index")]]
    )
    running_index_task = asyncio.create_task(
        index_process(bot, user_id, chat_id, last_msg_id, kb, cancel_state)
    )

    try:
        await running_index_task
    finally:
        running_index_task = None

async def index_process(bot, user_id, chat_id, last_msg_id, kb, cancel_state, start_id=1):
    from pyrogram.types import Message  # Import here for clarity and to fix the issue
    
    msg = await bot.send_message(user_id, "Processing Index... ⏳", reply_markup=kb)
    total_files = 0
    error_files = 0
    batch_size = 80
    processed = set()

    try:
        async with lock:
            for current_start in range(start_id, last_msg_id + 1, batch_size):
                if cancel_state["cancel"]:  # Check for cancellation
                    await msg.edit(f"Indexing canceled. Total files saved: {total_files}. Errors: {error_files}")
                    return

                end_id = min(current_start + batch_size - 1, last_msg_id)
                remaining = last_msg_id - end_id

                try:
                    messages = await bot.get_messages(chat_id, range(current_start, end_id + 1))
                except FloodWait as e:
                    LOGGER.warning("FloodWait while indexing: %s", e)
                    await asyncio.sleep(e.value)
                    continue
                except Exception as e:
                    LOGGER.warning("Error fetching messages: %s", e)
                    continue

                for message in messages:
                    if not isinstance(message, Message):  # Use the correct type
                        LOGGER.warning("Invalid message object encountered: %s", message)
                        continue

                    for file_type in ("document", "video", "audio"):
                        media = getattr(message, file_type, None)
                        if media and hasattr(message, "id") and message.id not in processed:
                            try:
                                file_name = media.file_name or "Unnamed"
                                file_name = edit_caption(file_name)
                                media.file_type = file_type
                                media.caption = file_name

                                LOGGER.info(f"Attempting to save file: Name={file_name}, Type={file_type}, ID={media.file_id}")

                                result = await save_file(media)  # Assuming `save_file` returns a success status

                                if result:
                                    total_files += 1
                                    processed.add(message.id)
                                    LOGGER.info(f"File saved successfully: {file_name}")
                                else:
                                    LOGGER.warning(f"save_file returned invalid result for file: {file_name}")
                            except Exception as e:
                                LOGGER.error(f"Error saving file: {e}", exc_info=True)
                                error_files += 1

                percent_done = (end_id / last_msg_id) * 100
                await msg.edit(
                    f"Processed {end_id}/{last_msg_id} messages.\n"
                    f"Files saved: {total_files}\n"
                    f"Errors: {error_files}\n"
                    f"Remaining messages: {remaining}\n"
                    f"Progress: {percent_done:.2f}%",
                    reply_markup=kb
                )

            await msg.edit(f"Indexing completed. Total files saved: {total_files}. Errors: {error_files}")
    except Exception as e:
        LOGGER.exception(e)
        await msg.edit(f"Error: {e}")


@Client.on_callback_query(filters.regex(r"^cancel-index"))
async def cancel_index_callback(bot, query):
    global running_index_task
    if running_index_task:
        cancel_state = running_index_task.get_coro().cr_frame.f_locals["cancel_state"]
        cancel_state["cancel"] = True
        await query.message.edit("Indexing task has been canceled.")
    else:
        await query.message.edit("No indexing task is currently running.")

@Client.on_message(filters.command(["skip"]) & filters.user(ADMINS))
async def skip_index(bot, message):
    global running_index_task

    if running_index_task:
        await message.reply("Another indexing task is already running. Please cancel it first.")
        return

    try:
        args = message.text.split()
        if len(args) != 2 or not args[1].isdigit():
            await message.reply("Usage: /skip <message_id>")
            return

        start_id = int(args[1])
        if start_id < 1:
            await message.reply("Message ID must be greater than 0.")
            return

        if not message.reply_to_message:
            await message.reply("Please reply to the last message of the channel you want to index.")
            return

        last_msg_id = message.reply_to_message.forward_from_message_id
        chat_id = message.reply_to_message.forward_from_chat.username or message.reply_to_message.forward_from_chat.id

        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel-index")]]
        )
        running_index_task = asyncio.create_task(index_process(bot, message.chat.id, chat_id, last_msg_id, kb, {"cancel": False}, start_id=start_id))
        await message.reply(f"Indexing started from message ID {start_id}.")
    except Exception as e:
        LOGGER.exception(e)
        await message.reply(f"Error starting indexing: {e}")

@Client.on_message(filters.command(["delete"]) & filters.user(ADMINS))
async def delete_files(bot, message):
    if not message.reply_to_message:
        await message.reply("Please reply to a file to delete.")
        return

    org_msg = message.reply_to_message
    for file_type in ("document", "video", "audio"):
        media = getattr(org_msg, file_type, None)
        if media:
            try:
                del_file = await delete_file(media)
                if del_file == "Not Found":
                    await message.reply(f"`{media.file_name}` not found in database.")
                else:
                    await message.reply(f"`{media.file_name}` deleted from database.")
            except Exception as e:
                LOGGER.warning("Error deleting file: %s", e)
