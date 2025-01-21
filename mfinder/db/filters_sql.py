import threading
import asyncio
from sqlalchemy import create_engine, Column, TEXT, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL, LOGGER

BASE = declarative_base()

class Filters(BASE):
    __tablename__ = "filters"
    filters = Column(String(255), primary_key=True)
    message = Column(TEXT)

    def __init__(self, filters, message):
        self.filters = filters
        self.message = message

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

async def add_filter(filters, message):
    with INSERTION_LOCK:
        try:
            fltr = SESSION.query(Filters).filter(Filters.filters.ilike(filters)).one()
        except NoResultFound:
            fltr = Filters(filters=filters, message=message)
            SESSION.add(fltr)
            SESSION.commit()
            return True

async def is_filter(filters):
    with INSERTION_LOCK:
        try:
            fltr = SESSION.query(Filters).filter(Filters.filters.ilike(filters)).one()
            return fltr
        except NoResultFound:
            return False

async def rem_filter(filters):
    with INSERTION_LOCK:
        try:
            fltr = SESSION.query(Filters).filter(Filters.filters.ilike(filters)).one()
            SESSION.delete(fltr)
            SESSION.commit()
            return True
        except NoResultFound:
            return False

async def list_filters():
    try:
        fltrs = SESSION.query(Filters.filters).all()
        return [fltr[0] for fltr in fltrs]
    except NoResultFound:
        return False
    finally:
        SESSION.close()