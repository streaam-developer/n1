# Telegram Media Finder

A telegram bot to find files saved in its database.

Re-written version of [Media Search bot](https://github.com/Mahesh0253/Media-Search-bot)

## Features

- Precise search option for more accurate results.
- Auto index files from given database channel/group.
- User settings for customization.
- Admin settings within the bot.
- Show search results as Button or List or List-Hyperlink.
- Manual index of files from channels.
- Supports document, video and audio file formats with file name caption support.
- Add manual text filters.
- Add username in file caption.
- Ban/Unban users.
- Broadcast to users.
- Auto delete files after a certain time.
- Force Subscription option.
- Option for Custom Caption
- Get logs / Restart from within the bot.

## Environment Variables

Required Variables

- `BOT_TOKEN`: Create a bot using [@BotFather](https://telegram.dog/BotFather), and get the Telegram API token.
- `APP_ID`: Get this value from [telegram.org](https://my.telegram.org/apps).
- `API_HASH`: Get this value from [telegram.org](https://my.telegram.org/apps).
- `DB_CHANNELS`: ID of database channel or group. Separate multiple IDs by space
- `OWNER_ID`: User ID of owner.
- `ADMINS`: User ID of Admins. Separate multiple Admins by space.
- `DB_URL`: Link to connect postgresql database (setup details given below).

## Database Setup

```bash
# Install postgresql:
sudo apt-get update && sudo apt-get install postgresql

# Change to the postgres user:
sudo su - postgres

# Create a new database user (change YOUR_USER appropriately):
createuser -P -s -e sonu
# This will be followed by you needing to input your password.

# create a new database table:
createdb -O sonu sonu
#Change YOUR_USER and YOUR_DB_NAME appropriately.

# finally:
psql -h localhost -p 5432 -d sonu -U sonu

#This will allow you to connect to your database via your terminal.
By default, YOUR_HOST should be `localhost` & 5432 should be `5432`.

You should now be able to build your database URI. This will be:
sqldbtype://username:password@hostname:port/db_name

Replace your sqldbtype, username, password, hostname (localhost?), port (5432?), and db name in .env file.
```

## Deployment

Run Locally / On VPS

```bash
# Clone this repo
git clone https://github.com/EL-Coders/mediafinder

# cd folder
cd mediafinder

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
venv\Scripts\activate # For Windows
source venv/bin/activate # For Linux or MacOS

# Install Packages
pip3 install -r requirements.txt

# Copy .env.sample file & add variables
cp .env.sample .env

# Run bot
python3 -m mfinder
```

If you want to modify start & help messages, copy [`sample_const.py`](sample_const.py) to `const.py` and do the changes.

```bash
cp sample_const.py const.py
```

## Support

Feedback or Support

Join our updates channel to get latest updates about our bots [EL Updates](https://t.me/ELUpdates)

If you have any feedback or to report any issues, please reach out to us at [EL Support](https://t.me/ELSupport)

## License

[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://github.com/EL-Coders/mediafinder/blob/main/LICENSE)

## Contributing

Contributions are always welcome, but please test your code before pushing!

Also, kindly adhere to this project's `code of conduct`.
