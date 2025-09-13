import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
DB_URL = os.getenv('DATABASE_URL')

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# set up the databse
def get_db():
    '''
        Setting up the database
    '''

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# for sqlite
# engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
# Base.metadata.create_all(bind=engine)
