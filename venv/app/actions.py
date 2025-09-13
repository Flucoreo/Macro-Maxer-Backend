import os
import logging
from datetime import date

from dotenv import load_dotenv
from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.schemas import UserCreate, UserReturn, UserPreferences, UserPasswordChange, UserPassword
from app.db.db_models import UserModel
from app.auth import get_password_hash, hash_refresh_token, verify_password


load_dotenv()
myKey = os.getenv('API_KEY')
client = genai.Client(api_key=f'{myKey}')


def api_call(user_prompt: str) -> str:

    '''

    Function for calling Gemini 2.5 Flash API to get the nutrition content of a given recipe or meal

    '''

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "nutrition_prompt.txt")

    system_content = open(file_path)
    system_prompt = system_content.read()

    # Define the grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    try:
        logging.info("Attempting to call the Gemini API...")
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=f"{system_prompt} \n {user_prompt}", config=config
        )
        logging.info("Gemini API call successful.")
        system_content.close()
        return response.text
    except Exception as e:
        system_content.close()
        raise e


def create_user(user: UserCreate, token: str, db: Session) -> UserReturn:

    '''

    Function for creating a user account

    '''

    # check if useremail already exists in database
    existing_user = db.query(UserModel).filter(UserModel.useremail == user.useremail).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use.")

    # Hash the password and refresh token before storing
    hashed_password = get_password_hash(user.userpassword)
    hashed_refresh_token = hash_refresh_token(token)

    # Create a dictionary with the user data and the hashed password
    user_data = user.dict()
    user_data["userpassword"] = hashed_password
    user_data.update({"disabled": False})
    user_data.update({"refresh_token": hashed_refresh_token})

    # if email is unique, add the user
    try:
        db_user = UserModel(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserReturn.from_orm(db_user).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user to database -> {e}") from e


def replace_refresh_token(user_id: int, token: str, db: Session) -> bool:

    '''
    
    Replacing old user refresh tokens with new ones in the database when the user logs in again
    
    '''

    db_user = db.get(UserModel, user_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="User doesn't Exist.")

    hashed_refresh_token = hash_refresh_token(token)

    try:
        setattr(db_user, "refresh_token", hashed_refresh_token)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update refresh token -> {e}") from e

    return True


def delete_refresh_token(request: Request, response: Response, db: Session) -> bool:

    '''
    
    Take a refresh token and delete it's match from the database
    
    '''

    # get the refresh token
    token = request.cookies.get("refreshToken")

    if not token:
        raise HTTPException(status_code=401, detail="Can not delete refresh token, none provided.")

    # delete refresh tokenn from data abase
    hashed_refresh_token = hash_refresh_token(token)
    try:
        entry = db.query(UserModel).filter(UserModel.refresh_token == hashed_refresh_token).first()
        if not entry:
            raise HTTPException(status_code=401, detail="Refresh token not found in database.")
        entry.refresh_token = ""
        db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete refresh token -> {e}") from e

    # delete both the access and refresh token from cookies
    response.delete_cookie(key="accessToken", path="/")
    response.delete_cookie(key="refreshToken", path="/auth/refresh")

    return True


def get_user_preferences(user: UserReturn, db: Session):

    '''
    
    Get the user's nutrition preferences from the database

    '''

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        user_preferences = db_user.preferences
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed get user preferences -> {e}") from e

    return user_preferences


def save_user_preferences(user: UserReturn, user_preferences: UserPreferences, db: Session):

    '''
    
    Save the user's nutrition preferences in the database

    '''

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        setattr(db_user, "preferences", user_preferences.dict(by_alias=True))
        db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed update user preferences -> {e}") from e

    return user_preferences


def change_password(user: UserReturn, passwords: UserPasswordChange, db: Session):

    '''
    
    Update the user's password
    
    '''

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        current_password_hash = db_user.userpassword

        if not verify_password(passwords.oldpassword, current_password_hash):
            raise HTTPException(status_code=400, detail="Invalid password.")

        new_password_hash = get_password_hash(passwords.password)

        setattr(db_user, "userpassword", new_password_hash)
        db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed update user password -> {e}") from e

    return user


def delete_account(password: UserPassword, user: UserReturn, db: Session):

    '''
    
    Delete a User's account
    
    '''

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        current_password_hash = db_user.userpassword

        if not verify_password(password.password, current_password_hash):
            raise HTTPException(status_code=400, detail="Invalid password.")

        db.delete(db_user)
        db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user account -> {e}") from e

    return True


def get_credits(user: UserReturn, db: Session):

    '''
    
    See how many credits the user has left

    '''

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        return db_user.credits
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user credits -> {e}") from e


def check_credits(user: UserReturn, db: Session):

    '''
    
    Check if the user has enough credits to be calling the gemini api
    
    '''

    remaining_credits = None

    try:
        db_user = db.get(UserModel, user['id'])
        if not db_user:
            raise HTTPException(status_code=400, detail="User doesn't exist in database.")

        # if its been 24h, reset to 5
        if db_user.last_reset < date.today():
            db_user.credits = 5
            db_user.last_reset = date.today()

        # After date reset, if user still has no credits
        if not db_user.credits >= 1:
            raise HTTPException(status_code=403, detail="User doesn't Have enough credits.")

        db_user.credits -= 1
        remaining_credits = db_user.credits
        db.commit()

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user credits -> {e}") from e

    return remaining_credits
