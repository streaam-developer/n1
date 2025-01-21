import uvloop
import os
import sys
import time
import asyncio
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
from mfinder import APP_ID, API_HASH, BOT_TOKEN

uvloop.install()

async def restart_bot():
    """
    Function to restart the bot by re-running the script.
    """
    print("Restarting the bot...")
    os.execv(sys.executable, ['python'] + sys.argv)

async def schedule_restart(interval_minutes, app):
    """
    Function to schedule the bot to restart at a given interval (in minutes).
    """
    while True:
        await asyncio.sleep(interval_minutes * 60)  # Convert minutes to seconds
        await app.stop()
        await restart_bot()

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
        print(
            f"{me.first_name} - @{me.username} - Pyrogram v{__version__} (Layer {layer}) - Started..."
        )

        # Start the restart scheduler
        asyncio.create_task(schedule_restart(30, app))

        await idle()
        print(f"{me.first_name} - @{me.username} - Stopped !!!")

if __name__ == "__main__":
    asyncio.run(main())