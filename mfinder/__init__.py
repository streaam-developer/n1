import os
import re
import logging
import logging.config
from dotenv import load_dotenv


load_dotenv()

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

id_pattern = re.compile(r"^.\d+$")

# vars
APP_ID = os.environ.get("APP_ID", "904789")
API_HASH = os.environ.get("API_HASH", "2262ef67ced426b9eea57867b11666a1")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6233167923:AAHnvFQBJ7YlwpwfhYv9ZTD98HjgYRFeYxg")
DB_URL = os.environ.get("DB_URL", "mysql+mysqldb://mediafi-35303337d0b6:mediafia1@mysql.gb.stackcp.com:64201/mediafi-35303337d0b6")
OWNER_ID = int(os.environ.get("OWNER_ID", "6597445442"))
ADMINS = [
    int(user) if id_pattern.search(user) else user
    for user in os.environ.get("ADMINS", "5791145987 5764988016").split()
] + [OWNER_ID]
DB_CHANNELS = [
    int(ch) if id_pattern.search(ch) else ch
    for ch in os.environ.get("DB_CHANNELS", "-1002450614102").split()
]

try:
    import const
except Exception:
    import sample_const as const

START_MSG = const.START_MSG
START_KB = const.START_KB
HELP_MSG = const.HELP_MSG
HELP_KB = const.HELP_KB

ASKFSUBINGRP = bool(os.environ.get('ASKFSUBINGRP', 1))
JOINREQ_MSG = bool(os.environ.get('JOINREQ_MSG', False))

auth_channel = os.environ.get('AUTH_CHANNEL', '-1002348104910')  # public channel 
second_auth_channel = os.environ.get('SECOND_AUTH_CHANNEL', '-1002346388593')  # Add the second auth channel or Group (should private)
third_auth_channel = os.environ.get('THIRD_AUTH_CHANNEL', '-1002348104910')  # Add the third auth channel or Group (should private)
AUTH_LINK = os.environ.get('AUTH_LINK', 'https://t.me/+gwfbTH8gUq5hNDZl')

AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
SECOND_AUTH_CHANNEL = int(second_auth_channel) if second_auth_channel and id_pattern.search(second_auth_channel) else None
FSUB_CHANNELS = int(third_auth_channel) if third_auth_channel and id_pattern.search(third_auth_channel) else None
THIRD_AUTH_CHANNEL = int(third_auth_channel) if third_auth_channel and id_pattern.search(third_auth_channel) else None


#first shortlink
SHORTLINK_URL = os.environ.get('FIRST_SHORTLINK_URL', 'anylinks.in')
SHORTLINK_API = os.environ.get('FIRST_SHORTLINK_API', '6fbf2472d51f7067dee2ad8ab1631f26606afad4')

#second shortlink 
SECOND_SHORTLINK_URL = os.environ.get('SECOND_SHORTLINK_URL', 'anylinks.in')
SECOND_SHORTLINK_API = os.environ.get('SECOND_SHORTLINK_API', '6fbf2472d51f7067dee2ad8ab1631f26606afad4')

#third shortlink
THIRD_SHORTLINK_URL = os.environ.get('THIRD_SHORTLINK_URL', 'anylinks.in')
THIRD_SHORTLINK_API = os.environ.get('THIRD_SHORTLINK_API', '6fbf2472d51f7067dee2ad8ab1631f26606afad4')

SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "adrinolinks.in")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "2c5ced55130160c243e8cc82dcb8d0e3afd89fc1")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
IS_VERIFY = os.environ.get("IS_VERIFY", "True")
TUT_VID = os.environ.get("TUT_VID","https://t.me/how2dow/5")
BOTUSERNAME = os.environ.get("BOTUSERNAME", "movie_downloaderebot")


#verify tutorial 
VERIFY_TUTORIAL = os.environ.get('FIRST_VERIFY_TUTORIAL', 'https://t.me/how2dow/57')
SECOND_VERIFY_TUTORIAL = os.environ.get('SECOND_VERIFY_TUTORIAL', 'https://t.me/how2dow/55')
THIRD_VERIFY_TUTORIAL = os.environ.get('THIRD_VERIFY_TUTORIAL', 'https://t.me/how2dow/76')


# logging Conf
logging.config.fileConfig(fname="config.ini", disable_existing_loggers=False)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
