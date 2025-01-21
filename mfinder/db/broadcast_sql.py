
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
    user_id = Column(BigInteger, primary_key=True)  # Primary key
    user_name = Column(TEXT)
    chat_id = Column(BigInteger, nullable=False)  # Add chat_id column

    def __init__(self, user_id, user_name, chat_id):
        self.user_id = user_id
        self.user_name = user_name
        self.chat_id = chat_id

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

async def add_join_request(user_id, chat_id):
    """Add a join request to the database."""
    with INSERTION_LOCK:
        try:
            # Check if the join request already exists
            result = SESSION.query(Broadcast).filter_by(user_id=user_id, chat_id=chat_id).one_or_none()
            if not result:
                # Add a new join request
                new_request = Broadcast(user_id=user_id, user_name=None, chat_id=chat_id)
                SESSION.add(new_request)
                SESSION.commit()
        except Exception as e:
            SESSION.rollback()
            raise e

async def check_join_request(user_id, chat_id):
    """Check if a join request exists in the database."""
    with INSERTION_LOCK:
        try:
            result = SESSION.query(Broadcast).filter_by(user_id=user_id, chat_id=chat_id).one_or_none()
            return result is not None
        except Exception as e:
            SESSION.rollback()
            raise e
        
async def delete_all_join_requests():
    """Delete all join requests from the database."""
    with INSERTION_LOCK:
        try:
            SESSION.query(Broadcast).delete()
            SESSION.commit()
        except Exception as e:
            SESSION.rollback()
            raise e
