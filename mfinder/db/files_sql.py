import threading
from sqlalchemy import create_engine, or_, func, and_
from sqlalchemy import Column, TEXT, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL, LOGGER
from mfinder.utils.helpers import unpack_new_file_id
from sqlalchemy import create_engine, Column, String, Integer, Boolean, BigInteger, Numeric

BASE = declarative_base()


class Files(BASE):
    __tablename__ = "files"
    file_name = Column(TEXT, primary_key=True)
    file_id = Column(String(255))
    file_ref = Column(String(255))
    file_size = Column(Numeric)
    file_type = Column(String(255))
    mime_type = Column(String(255))
    caption = Column(String(255))

    def __init__(
        self, file_name, file_id, file_ref, file_size, file_type, mime_type, caption
    ):
        self.file_name = file_name
        self.file_id = file_id
        self.file_ref = file_ref
        self.file_size = file_size
        self.file_type = file_type
        self.mime_type = mime_type
        self.caption = caption


def start() -> scoped_session:
    engine = create_engine(DB_URL, poolclass=QueuePool)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


SESSION = start()
INSERTION_LOCK = threading.RLock()


import re

# Function to clean the file name by removing unwanted words, links, and @containing words
def clean_file_name(file_name):
    # Remove words containing '@' and links (starting with http:// or https://)
    file_name = re.sub(r'\b\w+@\w+\.\w+\b', '', file_name)  # Remove words like '@example'
    file_name = re.sub(r'http[s]?://\S+', '', file_name)  # Remove links
    file_name = re.sub(r'\b(?:unwanted_word1|unwanted_word2|unwanted_word3)\b', '', file_name)  # Remove specific unwanted words
    
    # Remove extra spaces and return the cleaned file name
    return ' '.join(file_name.split())

async def save_file(media):
    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    # Clean the file name before saving
    cleaned_file_name = clean_file_name(media.file_name)
    
    with INSERTION_LOCK:
        try:
            file = SESSION.query(Files).filter_by(file_id=file_id).one()
            LOGGER.warning("%s is already saved in the database", cleaned_file_name)
        except NoResultFound:
            try:
                file = SESSION.query(Files).filter_by(file_name=cleaned_file_name).one()
                LOGGER.warning("%s is already saved in the database", cleaned_file_name)
            except NoResultFound:
                file = Files(
                    file_name=cleaned_file_name,
                    file_id=file_id,
                    file_ref=file_ref,
                    file_size=media.file_size,
                    file_type=media.file_type,
                    mime_type=media.mime_type,
                    caption=media.caption if media.caption else None,
                )
                LOGGER.info("%s is saved in database", cleaned_file_name)
                SESSION.add(file)
                SESSION.commit()
                return True
            except Exception as e:
                LOGGER.warning(
                    "Error occurred while saving file in database: %s", str(e)
                )
                SESSION.rollback()
                return False
        except Exception as e:
            LOGGER.warning("Error occurred while saving file in database: %s", str(e))
            SESSION.rollback()
            return False

async def get_filter_results(query, page=1, per_page=10):
    try:
        with INSERTION_LOCK:
            offset = (page - 1) * per_page
            search = query.split()
            conditions = []
            for word in search:
                conditions.append(
                    or_(
                        Files.file_name.ilike(f"%{word}%"),
                        Files.caption.ilike(f"%{word}%"),
                    )
                )
            combined_condition = and_(*conditions)
            files_query = (
                SESSION.query(Files)
                .filter(combined_condition)
                .order_by(Files.file_name)
            )
            total_count = files_query.count()
            files = files_query.offset(offset).limit(per_page).all()
            return files, total_count
    except Exception as e:
        LOGGER.warning("Error occurred while retrieving filter results: %s", str(e))
        return [], 0


async def get_precise_filter_results(query, page=1, per_page=10):
    try:
        with INSERTION_LOCK:
            offset = (page - 1) * per_page
            search = query.split()
            conditions = []
            for word in search:
                conditions.append(
                    or_(
                        func.concat(" ", Files.file_name, " ").ilike(f"% {word} %"),
                        func.concat(" ", Files.caption, " ").ilike(f"% {word} %"),
                    )
                )
            combined_condition = and_(*conditions)
            files_query = (
                SESSION.query(Files)
                .filter(combined_condition)
                .order_by(Files.file_name)
            )
            total_count = files_query.count()
            files = files_query.offset(offset).limit(per_page).all()
            return files, total_count
    except Exception as e:
        LOGGER.warning("Error occurred while retrieving filter results: %s", str(e))
        return [], 0


async def get_file_details(file_id):
    try:
        with INSERTION_LOCK:
            file_details = SESSION.query(Files).filter_by(file_id=file_id).all()
            return file_details
    except Exception as e:
        LOGGER.warning("Error occurred while retrieving file details: %s", str(e))
        return []


async def delete_file(media):
    file_id, file_ref = unpack_new_file_id(media.file_id)
    try:
        with INSERTION_LOCK:
            file = SESSION.query(Files).filter_by(file_id=file_id).first()
            if file:
                SESSION.delete(file)
                SESSION.commit()
                return True
            return "Not Found"
            LOGGER.warning("File to delete not found: %s", str(file_id))
    except Exception as e:
        LOGGER.warning("Error occurred while deleting file: %s", str(e))
        SESSION.rollback()
        return False

async def count_files():
    try:
        with INSERTION_LOCK:
            total_count = SESSION.query(Files).count()
            return total_count
    except Exception as e:
        LOGGER.warning("Error occurred while counting files: %s", str(e))
        return 0