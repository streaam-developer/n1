import threading
from sqlalchemy import create_engine
from sqlalchemy import Column, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL
from sqlalchemy import create_engine, Column, String, Integer, Boolean, BigInteger, Numeric
BASE = declarative_base()
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

class Filters(BASE):
    __tablename__ = "filters"
    filters = Column(String(255), primary_key=True)
    message = Column(TEXT)

    def __init__(self, filters, message):
        self.filters = filters
        self.message = message


class Files(BASE):
    __tablename__ = 'files'
    file_name = Column(String(255), primary_key=True)  # Define a length for VARCHAR
    file_id = Column(Text)
    file_ref = Column(Text)
    file_size = Column(Numeric)
    file_type = Column(Text)
    mime_type = Column(Text)
    caption = Column(Text)

    def __init__(self, filters, message):
        self.filters = filters
        self.message = message


def start() -> scoped_session:
    engine = create_engine(
    DB_URL,
    pool_size=20,         # Number of connections in the pool
    max_overflow=10,      # Extra connections beyond the pool size
    pool_timeout=30,      # Timeout in seconds for getting a connection
    pool_recycle=3600,    # Recycle connections every hour
    pool_pre_ping=True,   # Ensure connections are alive before using
)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


SESSION = start()
INSERTION_LOCK = threading.RLock()


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
