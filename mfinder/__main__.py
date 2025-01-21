import uvloop
import asyncio
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
from mfinder import APP_ID, API_HASH, BOT_TOKEN, OWNER_ID
import os

uvloop.install()


async def send_restart_message(app):
    """
    Function to send a message to the owner indicating a successful restart.
    """
    try:
        await app.send_message(chat_id=OWNER_ID, text="Bot is restarting...")
    except Exception as e:
        print(f"Failed to send restart message: {e}")


async def restart_bot(app):
    """
    Restart the bot without closing the terminal.
    """
    print("Restarting the bot...")
    await send_restart_message(app)
    await app.stop()  # Stop the current bot session
    await asyncio.sleep(1)  # Give it a second before restarting
    await app.start()  # Restart the bot session
    print("Bot restarted successfully.")


async def schedule_restart(interval_minutes, app):
    """
    Function to schedule the bot to restart at a given interval (in minutes).
    """
    while True:
        await asyncio.sleep(interval_minutes * 60)  # Wait for the interval
        await restart_bot(app)  # Restart the bot


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
        asyncio.create_task(schedule_restart(1, app))  # Restart every 1 minute

        await idle()
        print(f"{me.first_name} - @{me.username} - Stopped !!!")


if __name__ == "__main__":
    asyncio.run(main())
