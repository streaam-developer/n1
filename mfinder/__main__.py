import uvloop
import asyncio
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
from mfinder import APP_ID, API_HASH, BOT_TOKEN, OWNER_ID

uvloop.install()

 # Replace with your actual Telegram user ID

async def send_restart_message(app):
    """
    Function to send a message to the owner indicating a successful restart.
    """
    try:
        await app.send_message(chat_id=OWNER_ID, text="Bot has restarted successfully.")
    except Exception as e:
        print(f"Failed to send restart message: {e}")

async def restart_bot(app):
    """
    Function to restart the bot by stopping and starting the app instance.
    """
    await app.stop()  # Stop the current instance
    print("Bot is restarting...")
    await app.start()  # Start the instance again
    await send_restart_message(app)

async def schedule_restart(interval_minutes, app):
    """
    Function to schedule the bot to restart at a given interval (in minutes).
    """
    while True:
        await asyncio.sleep(interval_minutes * 60)  # Convert minutes to seconds
        await restart_bot(app)

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
        asyncio.create_task(schedule_restart(1, app))  # Restart every 60 minutes

        await idle()
        print(f"{me.first_name} - @{me.username} - Stopped !!!")

if __name__ == "__main__":
    asyncio.run(main())
