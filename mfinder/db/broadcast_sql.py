import threading
import asyncio
from sqlalchemy import create_engine, Column, TEXT, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL, LOGGER

BASE = declarative_base()

class Broadcast(BASE):
    __tablename__ = "broadcast"
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(TEXT)

    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name

def start() -> scoped_session:
    engine = create_engine(DB_URL, pool_size=5, max_overflow=10)
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

async def add_user(user_id, user_name):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(Broadcast).filter_by(user_id=user_id).one()
        except NoResultFound:
            usr = Broadcast(user_id=user_id, user_name=user_name)
            SESSION.add(usr)
            SESSION.commit()

async def is_user(user_id):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(Broadcast).filter_by(user_id=user_id).one()
            return usr.user_id
        except NoResultFound:
            return False

async def query_msg():
    try:
        query = SESSION.query(Broadcast.user_id).order_by(Broadcast.user_id)
        return query.all()
    finally:
        SESSION.close()

async def del_user(user_id):
    with INSERTION_LOCK:
        try:
            usr = SESSION.query(Broadcast).filter_by(user_id=user_id).one()
            SESSION.delete(usr)
            SESSION.commit()
        except NoResultFound:
            pass

async def count_users():
    try:
        return SESSION.query(Broadcast).count()
    finally:
        SESSION.close()