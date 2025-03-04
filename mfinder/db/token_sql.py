from sqlalchemy import create_engine, Column, BigInteger, Boolean, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from mfinder import *
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import IntegrityError

# SQLAlchemy base and table definition
Base = declarative_base()

from datetime import datetime, timedelta

class Verify(Base):
    __tablename__ = 'verify'

    user_id = Column(Integer, primary_key=True)
    is_verified = Column(Boolean, default=False)
    verified_time = Column(BigInteger, default=0)
    verify_token = Column(String(255), default='')
    link = Column(String(255), default='')
    expiry_time = Column(BigInteger, default=0)  # Add this column

# Token validation function
async def is_token_valid(user_id, token):
    session = Session()
    try:
        verify_entry = session.query(Verify).filter_by(user_id=user_id).one_or_none()
        if verify_entry and verify_entry.verify_token == token:
            current_time = int(datetime.utcnow().timestamp())
            return current_time <= verify_entry.expiry_time  # Check token expiry
        return False
    finally:
        session.close()

# Database connection setup
engine = create_engine(DB_URL, poolclass=QueuePool)
Session = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

async def db_verify_status(user_id):
    session = Session()
    try:
        verify_entry = session.query(Verify).filter_by(user_id=user_id).one()
        return {
            'is_verified': verify_entry.is_verified,
            'verified_time': verify_entry.verified_time,
            'verify_token': verify_entry.verify_token,
            'link': verify_entry.link
        }
    except Exception:
        return default_verify
    finally:
        session.close()

async def db_update_verify_status(user_id, verify):
    session = Session()
    try:
        verify_entry = session.query(Verify).filter_by(user_id=user_id).one_or_none()
        
        # If the entry exists, update it
        if verify_entry:
            verify_entry.is_verified = verify['is_verified']
            verify_entry.verified_time = verify['verified_time']
            verify_entry.verify_token = verify['verify_token']
            verify_entry.link = verify['link']
        else:
            # If no entry exists, create a new one
            new_entry = Verify(
                user_id=user_id,
                is_verified=verify['is_verified'],
                verified_time=verify['verified_time'],
                verify_token=verify['verify_token'],
                link=verify['link']
            )
            session.add(new_entry)

        session.commit()
        
    except IntegrityError as e:
        # Handle unique constraint violation by updating the record instead
        session.rollback()  # Rollback the transaction if an error occurs
        if "Duplicate entry" in str(e):
            # If a duplicate entry error occurs, try updating the existing record
            session.query(Verify).filter_by(user_id=user_id).update({
                'is_verified': verify['is_verified'],
                'verified_time': verify['verified_time'],
                'verify_token': verify['verify_token'],
                'link': verify['link']
            })
            session.commit()
        else:
            raise e  # Raise the exception if it's not a duplicate error
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
