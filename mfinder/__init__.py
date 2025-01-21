import os
import re
import logging
import logging.config
from dotenv import load_dotenv


load_dotenv()


id_pattern = re.compile(r"^.\d+$")

# vars
APP_ID = os.environ.get("APP_ID", "904789")
API_HASH = os.environ.get("API_HASH", "2262ef67ced426b9eea57867b11666a1")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "5120091936:AAGX5L29-BRpyA_mv7j-A60h_e8jvZF0JgM")
DB_URL = os.environ.get("DB_URL", "mysql+mysqldb://ipapbb-35303337fc40:ipapbb12@mysql.gb.stackcp.com:63198/ipapbb-35303337fc40")
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


# logging Conf
logging.config.fileConfig(fname="config.ini", disable_existing_loggers=False)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
