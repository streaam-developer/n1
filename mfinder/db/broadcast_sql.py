
import threading
from sqlalchemy import create_engine, Column, TEXT, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL

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

from sqlalchemy.orm.exc import NoResultFound

async def check_join_request(self, user_id, chat_id):
    """
    Check if the user has a join request in the database.

    Args:
        user_id (int): The ID of the user.
        chat_id (int): The ID of the chat.

    Returns:
        bool: True if a join request exists, False otherwise.
    """
    try:
        # Query the database to check for a join request
        result = self.session.query(self.JoinRequest).filter_by(user_id=user_id, chat_id=chat_id).one_or_none()
        return result is not None  # True if a record exists, False otherwise
    except NoResultFound:
        return False
