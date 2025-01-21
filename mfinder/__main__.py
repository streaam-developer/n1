import uvloop
import asyncio
from pyrogram import Client, idle, __version__, filters
from pyrogram.raw.all import layer
from mfinder import APP_ID, API_HASH, BOT_TOKEN, OWNER_ID, ADMINS
import os
import sys
import logging

# Setup logger
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

uvloop.install()

# Manual Restart Command
@Client.on_message(filters.command(["restart"]) & filters.user(ADMINS))
async def restart(bot, update):
    LOGGER.warning("Restarting bot using /restart command")
    msg = await update.reply_text(text="__Restarting.....__")
    await asyncio.sleep(5)
    await msg.edit("__Bot restarted!__")
    os.execv(sys.executable, ["python3", "-m", "mfinder"] + sys.argv)


async def schedule_restart(interval_minutes):
    """
    Schedule automatic bot restarts every `interval_minutes` minutes.
    """
    while True:
        await asyncio.sleep(interval_minutes * 60)  # Wait for the interval
        LOGGER.info(f"Restarting bot automatically after {interval_minutes} minute(s)")
        os.execv(sys.executable, ["python3", "-m", "mfinder"] + sys.argv)


async def send_restart_message(app):
    """
    Notify the owner after a successful restart.
    """
    try:
        await app.send_message(chat_id=OWNER_ID, text="Bot has restarted successfully.")
        LOGGER.info("Restart message sent to the owner.")
    except Exception as e:
        LOGGER.error(f"Failed to send restart message: {e}")


async def main():
    plugins = dict(root="mfinder/plugins")
    app = Client(
        name="mfinder",
        api_id=APP_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=plugins,
    )

    async with app:
        me = await app.get_me()
        LOGGER.info(
            f"{me.first_name} - @{me.username} - Pyrogram v{__version__} (Layer {layer}) - Started..."
        )

        # Notify owner of a successful restart
        await send_restart_message(app)

        # Start the automatic restart scheduler
        asyncio.create_task(schedule_restart(1))  # Restart every 1 minute

        await idle()
        LOGGER.info(f"{me.first_name} - @{me.username} - Stopped!")


if __name__ == "__main__":
    asyncio.run(main())
