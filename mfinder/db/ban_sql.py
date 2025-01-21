import threading
import asyncio
from sqlalchemy import create_engine, Column, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL, LOGGER


BASE = declarative_base()

class BanList(BASE):
    __tablename__ = "banlist"
    user_id = Column(BigInteger, primary_key=True)

    def __init__(self, user_id):
        self.user_id = user_id

def start() -> scoped_session:
    engine = create_engine(DB_URL, poolclass=QueuePool)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))

SESSION = start()
INSERTION_LOCK = threading.RLock()

async def reconnect():
    """Reconnect to the database every 5 minutes."""
    while True:
        try:
            SESSION.remove()  # Remove the current session
            global SESSION
            SESSION = start()  # Recreate the session
            LOGGER.info("Reconnected to the database.")
        except Exception as e:
            LOGGER.warning("Reconnection failed: %s", str(e))
        
        await asyncio.sleep(300)  # Wait for 5 minutes (300 seconds)

async def ban_user(user_id):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(BanList).filter_by(user_id=user_id).one()
        except NoResultFound:
            usr = BanList(user_id=user_id)
            SESSION.add(usr)
            SESSION.commit()
            return True

async def is_banned(user_id):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(BanList).filter_by(user_id=user_id).one()
            return usr.user_id
        except NoResultFound:
            return False

async def unban_user(user_id):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(BanList).filter_by(user_id=user_id).one()
            SESSION.delete(usr)
            SESSION.commit()
            return True
        except NoResultFound:
            return False