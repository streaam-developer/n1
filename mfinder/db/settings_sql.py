import threading
from sqlalchemy import create_engine, Column, String, Integer, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm.exc import NoResultFound
from mfinder import DB_URL, LOGGER

BASE = declarative_base()

class AdminSettings(BASE):
    __tablename__ = "admin_settings"
    setting_name = Column(String(255), primary_key=True)
    auto_delete = Column(Integer)
    custom_caption = Column(String(255))  # Specify length for VARCHAR
    fsub_channel = Column(Integer)
    channel_link = Column(String)
    caption_uname = Column(String)
    repair_mode = Column(Boolean)

    def __init__(self, setting_name="default"):
        self.setting_name = setting_name
        self.auto_delete = 0
        self.custom_caption = None
        self.fsub_channel = None
        self.channel_link = None
        self.caption_uname = None
        self.repair_mode = False

class Settings(BASE):
    __tablename__ = "settings"
    user_id = Column(BigInteger, primary_key=True)
    precise_mode = Column(Boolean, default=False)
    button_mode = Column(Boolean, default=False)
    link_mode = Column(Boolean, default=True)  # Default `link_mode` to True
    list_mode = Column(Boolean, default=False)

    def __init__(self, user_id, precise_mode=False, button_mode=False, link_mode=True, list_mode=False):
        self.user_id = user_id
        self.precise_mode = precise_mode
        self.button_mode = button_mode
        self.link_mode = link_mode
        self.list_mode = list_mode

def start() -> scoped_session:
    engine = create_engine(DB_URL, poolclass=StaticPool)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))

SESSION = start()
INSERTION_LOCK = threading.RLock()

OWNER_ID = 6597445442  # Replace this with the actual owner ID

async def get_search_settings(user_id):
    try:
        with INSERTION_LOCK:
            settings = SESSION.query(Settings).filter_by(user_id=OWNER_ID).first()
            if not settings:
                # Fetch the owner's settings if user-specific settings do not exist
                settings = SESSION.query(Settings).filter_by(user_id=OWNER_ID).first()
            return settings
    except Exception as e:
        LOGGER.warning("Error getting search settings: %s ", str(e))
        return None

async def change_search_settings(user_id, precise_mode=None, button_mode=None, link_mode=None, list_mode=None):
    try:
        with INSERTION_LOCK:
            if user_id == OWNER_ID:
                # Owner updates settings for all users
                settings_list = SESSION.query(Settings).all()
                for settings in settings_list:
                    if precise_mode is not None:
                        settings.precise_mode = precise_mode
                    if button_mode is not None:
                        settings.button_mode = button_mode
                    if link_mode is not None:
                        settings.link_mode = link_mode
                    if list_mode is not None:
                        settings.list_mode = list_mode
                SESSION.commit()
            else:
                # Regular user updates their settings
                settings = SESSION.query(Settings).filter_by(user_id=OWNER_ID).first()
                if settings:
                    if precise_mode is not None:
                        settings.precise_mode = precise_mode
                    if button_mode is not None:
                        settings.button_mode = button_mode
                    if link_mode is not None:
                        settings.link_mode = link_mode
                    if list_mode is not None:
                        settings.list_mode = list_mode
                else:
                    new_settings = Settings(
                        user_id=user_id, precise_mode=precise_mode, button_mode=button_mode, link_mode=link_mode, list_mode=list_mode
                    )
                    SESSION.add(new_settings)
                SESSION.commit()
            return True
    except Exception as e:
        LOGGER.warning("Error changing search settings: %s ", str(e))

async def set_repair_mode(repair_mode):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.repair_mode = repair_mode
            session.commit()

    except Exception as e:
        LOGGER.warning("Error setting repair mode: %s ", str(e))

async def set_auto_delete(dur):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.auto_delete = dur
            session.commit()

    except Exception as e:
        LOGGER.warning("Error setting auto delete: %s ", str(e))

async def get_admin_settings():
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            return admin_setting
    except Exception as e:
        LOGGER.warning("Error getting admin settings: %s", str(e))

async def set_custom_caption(caption):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.custom_caption = caption
            session.commit()

    except Exception as e:
        LOGGER.warning("Error setting custom caption: %s ", str(e))

async def set_force_sub(channel):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.fsub_channel = channel
            session.commit()

    except Exception as e:
        LOGGER.warning("Error setting Force Sub channel: %s ", str(e))

async def set_channel_link(link):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.channel_link = link
            session.commit()

    except Exception as e:
        LOGGER.warning("Error adding Force Sub channel link: %s ", str(e))

async def get_channel():
    try:
        channel = SESSION.query(AdminSettings.fsub_channel).first()
        if channel:
            return channel[0]
        return False
    except NoResultFound:
        return False
    finally:
        SESSION.close()

async def get_link():
    try:
        link = SESSION.query(AdminSettings.channel_link).first()
        if link:
            return link[0]
        return False
    except NoResultFound:
        return False
    finally:
        SESSION.close()

async def set_username(username):
    try:
        with INSERTION_LOCK:
            session = SESSION()
            admin_setting = session.query(AdminSettings).first()
            if not admin_setting:
                admin_setting = AdminSettings(setting_name="default")
                session.add(admin_setting)
                session.commit()

            admin_setting.caption_uname = username
            session.commit()

    except Exception as e:
        LOGGER.warning("Error adding username: %s ", str(e))
