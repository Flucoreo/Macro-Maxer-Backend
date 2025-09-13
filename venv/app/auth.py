import os
import hashlib

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from jose import JWTError, jwt 
from passlib.context import CryptContext

from app.schemas import UserReturn, TokenData
from app.db.db_models import UserModel
from app.db.database import get_db


load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credential_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
)


def verify_password(given_password, hashed_password):
    '''
    Varify a user entered the right password 
    by comparing it to the password in the database
    '''
    return pwd_context.verify(given_password, hashed_password)


def get_password_hash(password):
    '''
    Hash a given password
    '''
    return pwd_context.hash(password)


def hash_refresh_token(token: str) -> str:
    '''
    Hash a given refresh token
    '''
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def retrieve_user_by_email(email: str, db: Session) -> UserReturn:
    '''
    Retrieve a user by its email. (including password hash, only for internal use)
    '''
    db_user = db.query(UserModel).filter(UserModel.useremail == email).first()

    if db_user:
        return UserReturn.from_orm(db_user).model_dump()

    return None


def authenticate_user(db: Session, email: str, userpassowrd: str) -> UserReturn:
    '''
    verify if a user exists, and if so, if the given password hash is correct
    '''

    db_user = db.query(UserModel).filter(UserModel.useremail == email).first()

    if not db_user:
        return False

    if not verify_password(userpassowrd, db_user.userpassword):
        return False

    return UserReturn.from_orm(db_user).model_dump()


def create_access_token(data: dict, expires_delta: timedelta | None = None, refresh: bool = False):
    '''
    Creating the access and refresh JWTs that encodes the userdata and expiring date
    '''
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    to_encode.update({"refresh": refresh})

    if refresh:
        encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, ALGORITHM)
    else:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

    return encoded_jwt


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserReturn:
    '''
    Take in a JTW, decode it, and check to see if the decoded user exists, if so return the user
    '''

    token = request.cookies.get("accessToken")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            raise credential_exception

        token_data = TokenData(username=user_email)
    except JWTError:
        raise credential_exception

    user = retrieve_user_by_email(token_data.username, db)
    if user is None:
        raise credential_exception

    return user


async def get_current_active_user(db: Session = Depends(get_db),
                                current_user: UserReturn = Depends(get_current_user)) -> UserReturn:
    '''
    Check if the user is disabled before granting access
    '''

    db_user = db.get(UserModel, current_user['id'])
    if db_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if db_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def verify_refresh_token(request: Request, db: Session = Depends(get_db)) -> UserReturn:

    '''
    When user access tokens expire, take in their refresh token and validate it
    '''

    # extract refresh token from cookies
    token = request.cookies.get("refreshToken")

    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required.")

    # ensure the refresh token belongs to a valid user (and if its expired [automatically])
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            raise credential_exception

        token_data = TokenData(username=user_email)
    except JWTError:
        raise credential_exception

    user = retrieve_user_by_email(token_data.username, db)
    if user is None:
        raise credential_exception

    # if the JWT is valid, ensure it is in the DB
    hashed_token = hash_refresh_token(token)
    db_user = db.get(UserModel, user['id'])

    if db_user is None or db_user.refresh_token != hashed_token:
        raise credential_exception

    return user
