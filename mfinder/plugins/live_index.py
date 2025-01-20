from pyrogram import Client, filters
from mfinder import DB_CHANNELS, LOGGER
from mfinder.db.files_sql import save_file
from mfinder.utils.helpers import edit_caption

media_filter = filters.document | filters.video | filters.audio


@Client.on_message(filters.chat(DB_CHANNELS) & media_filter)
async def live_index(bot, message):
    try:
        for file_type in ("document", "video", "audio"):
            media = getattr(message, file_type, None)
            if not media:
                continue
            file_name = media.file_name or "Unnamed"
            file_name = edit_caption(file_name)
            media.file_type = file_type
            media.caption = file_name
            await save_file(media)
    except Exception as e:
        LOGGER.warning("Error while saving file in live index: %s", e)
