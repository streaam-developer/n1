import random
import string
from datetime import datetime, timedelta, date
from mfinder import API, URL
from shortzy import Shortzy
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool
from mfinder import DB_URL

# Database Setup
BASE = declarative_base()

class Token(BASE):
    __tablename__ = "tokens"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    token = Column(String(255), nullable=False)
    expiry = Column(DateTime, nullable=False)
    is_verified = Column(String(10), default="no")  # 'yes' or 'no'

    def __init__(self, user_id, token, expiry):
        self.user_id = user_id
        self.token = token
        self.expiry = expiry

def start() -> scoped_session:
    engine = create_engine(
        DB_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))

SESSION = start()

# Utility Functions
async def get_verify_shorted_link(link):
    try:
        shortzy = Shortzy(api_key=API, base_site=URL)
        shortened_link = await shortzy.convert(link)
        return shortened_link
    except Exception as e:
        print(f"Error shortening link: {e}")
        return link  # Return original link if shortening fails

async def get_token(bot, userid, link):
    """
    Generate a new token for a user, replacing the old one if it exists.
    """
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    expiry = datetime.utcnow() + timedelta(days=1)  # Token valid for 1 day

    try:
        # Delete old token for this user
        old_token = SESSION.query(Token).filter_by(user_id=user.id).first()
        if old_token:
            SESSION.delete(old_token)
            SESSION.commit()

        # Save new token
        new_token = Token(user_id=user.id, token=token, expiry=expiry)
        SESSION.add(new_token)
        SESSION.commit()

        # Generate verification link
        link = f"{link}verify-{user.id}-{token}"
        shortened_verify_url = await get_verify_shorted_link(link)
        return str(shortened_verify_url)
    except Exception as e:
        print(f"Error generating token: {e}")
        SESSION.rollback()
        return None

async def check_token(bot, userid, token):
    """
    Check if the given token for the user is valid and not expired.
    """
    try:
        token_entry = (
            SESSION.query(Token)
            .filter_by(user_id=userid, token=token, is_verified="no")
            .one()
        )
        if token_entry.expiry > datetime.utcnow():
            return True
    except NoResultFound:
        return False
    except Exception as e:
        print(f"Error checking token: {e}")
    return False

async def verify_user(bot, userid, token):
    """
    Mark a token as verified for the user.
    """
    try:
        token_entry = (
            SESSION.query(Token)
            .filter_by(user_id=userid, token=token, is_verified="no")
            .one()
        )
        token_entry.is_verified = "yes"
        SESSION.commit()
    except NoResultFound:
        print(f"No valid token found for user {userid} with token {token}.")
    except Exception as e:
        print(f"Error verifying token: {e}")
        SESSION.rollback()

async def check_verification(bot, userid):
    """
    Check if the user has a valid verification (not expired).
    """
    try:
        token_entry = (
            SESSION.query(Token)
            .filter_by(user_id=userid, is_verified="yes")
            .first()
        )
        if token_entry and token_entry.expiry > datetime.utcnow():
            return True
    except Exception as e:
        print(f"Error checking verification for user {userid}: {e}")
    return False
