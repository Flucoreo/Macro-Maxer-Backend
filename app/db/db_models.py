import os
import json

from sqlalchemy import Column, Integer, String, Boolean, JSON, Date, func
from app.db.database import Base

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, "default_settings.json")
with open(file_path, "r") as f:
    settings = json.load(f)

class UserModel(Base):
    '''
    Database user model
    '''

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    useremail = Column(String(100), unique=True)
    userpassword = Column(String(200))
    disabled = Column(Boolean)
    refresh_token = Column(String(128))
    preferences = Column(JSON, nullable=False, default=lambda: settings.copy())
    credits = Column(Integer, nullable=False, default=5)
    last_reset = Column(Date, nullable=False, default=func.current_date())
