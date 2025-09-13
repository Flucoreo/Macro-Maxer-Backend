from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from redis.exceptions import RedisError
from rq import Queue
from rq.job import Job

from app.schemas import UserCreate, UserReturn, UserPreferences, UserPasswordChange, UserPassword, UserReturnCredits
from app.task import nutrient_worker
from app.db.database import get_db
from app.actions import (create_user,
                         replace_refresh_token,
                         delete_refresh_token,
                         get_user_preferences,
                         save_user_preferences,
                         change_password,
                         delete_account,
                         check_credits, 
                         get_credits)
from app.auth import (ACCESS_TOKEN_EXPIRE_MINUTES,
                      REFRESH_TOKEN_EXPIRE_DAYS,
                      create_access_token,
                      authenticate_user,
                      get_current_active_user,
                      verify_refresh_token)


router = APIRouter()


@router.post("/nutrition", response_model=None)
def start_nutrition_job(request: Request,
                        user_recipe: str,
                        user: UserReturn = Depends(get_current_active_user),
                        db: Session = Depends(get_db)):

    '''
    
    Add a job to get the nutrition breakdown to the redis queue
    
    '''

    try:
        credits_left = check_credits(user, db)
    except Exception as e:
        raise e

    try:
        redis_connection = request.app.state.redis
        task_queue = Queue("task_queue", connection=redis_connection)
        job_instance = task_queue.enqueue(nutrient_worker, user_recipe)
    except RedisError as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

    return {
        "success": True,
        "job_id": job_instance.id,
        "credits": credits_left
    }


@router.get("/nutrition", response_model=None)
def check_job_status(request: Request, job_id: str, user: UserReturn = Depends(get_current_active_user)):

    '''
    
    Allow user to monitor the status of their nutrition breakdown job
    
    '''

    redis_connection = request.app.state.redis

    try:
        job = Job.fetch(job_id, connection=redis_connection)
    except Exception as e:
        return {"status": f"job_not_found -> {e}"}

    if job.is_finished:
        return {"status": "finished", "result": job.result}
    elif job.is_failed:
        return {"status": "failed", "error": str(job.exc_info)}
    elif job.is_queued:
        return {"status": "queued"}
    elif job.is_started:
        return {"status": "started"}

    return {"status": "unknown"}


@router.post("/auth/signup", response_model=UserReturn)
async def sign_up(user: UserCreate, db: Session = Depends(get_db)) -> UserReturn:

    '''

    API enpoint for creating a user account and issuing access + refresh JWTs

    '''

    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days = REFRESH_TOKEN_EXPIRE_DAYS)

    # Important, we are encoding the useremail in the jwt even though it is under the title username
    access_token = create_access_token(
        data={"sub": user.useremail}, expires_delta=access_token_expires
    )

    refresh_token = create_access_token(
        data={"sub": user.useremail}, expires_delta=refresh_token_expires, refresh=True
    )

    # add the user to the database
    try:
        user_data = create_user(user, refresh_token, db)
    except Exception as e:
        raise e

    # return user data and JWTs
    response = JSONResponse(content=user_data)

    # send JWT access and refresh tokens as HTTP only cookies
    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return response


@router.post("/auth/login", response_model=UserReturn)
async def log_in(form_data: OAuth2PasswordRequestForm = Depends(),
                  db: Session = Depends(get_db)) -> UserReturn:

    '''

    API enpoint for logging in a user account and issuing access + refresh JWTs

    '''

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Incorrect User ID or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days = REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user['useremail']}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user['useremail']}, expires_delta=refresh_token_expires, refresh=True
    )

    # replace old refresh token with new one
    if not replace_refresh_token(user['id'], refresh_token, db):
        raise HTTPException(status_code=500, detail="Failed to update refresh token, login failed")

    # return user data and JWTs
    response = JSONResponse(content=user)

    # send JWT access and refresh tokens as HTTP only cookies
    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return response


@router.post("/auth/refresh", response_model=UserReturn)
async def refresh_tokens(user: UserReturn = Depends(verify_refresh_token)) -> UserReturn:

    '''

    API enpoint for taking user's refresh token and issuing a new access token

    '''

    if not user:
        raise HTTPException(
            status_code=500, detail="Unable to refresh token",
        )

    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user['useremail']}, expires_delta=access_token_expires
    )

    # return user data and JWTs
    response = JSONResponse(content=user)

    # send JWT access token as HTTP only cookies
    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return response


@router.post("/auth/logout", response_model=None)
async def log_out(request: Request, response: Response, db: Session = Depends(get_db)):

    '''
    
    API Endpoint to delete the user's refresh token when they log out
    
    '''

    if delete_refresh_token(request, response, db):
        return {
            "message": "Successfully logged out"
        }


@router.get("/whoami", response_model=UserReturnCredits)
async def whoami(user: UserReturn = Depends(get_current_active_user), db: Session = Depends(get_db)):

    '''

    API Endpoint to get data if logged in

    '''
    user_credits = get_credits(user, db)

    user.update({"credits": user_credits})

    return user


@router.get("/preferences", response_model=UserPreferences)
async def retrieve_user_preferences(user: UserReturn = Depends(get_current_active_user),
                                    db: Session = Depends(get_db)) -> UserPreferences:

    '''

    API Endpoint to get the user nutrition preferences from the database

    '''

    try:
        preferences_settings = get_user_preferences(user, db)
    except Exception as e:
        raise e

    return preferences_settings


@router.post("/preferences", response_model=UserPreferences)
async def update_user_preferences(user_preferences: UserPreferences,
                             user: UserReturn = Depends(get_current_active_user),
                             db: Session = Depends(get_db)) -> UserPreferences:

    '''

    API Endpoint to update the user nutrition preferences in the database

    '''

    try:
        preferences_settings = save_user_preferences(user, user_preferences, db)
    except Exception as e:
        raise e

    return preferences_settings


@router.post("/update_password", response_model=UserReturn)
async def update_user_password(password_data: UserPasswordChange,
                                user: UserReturn = Depends(get_current_active_user),
                                db: Session = Depends(get_db)) -> UserReturn:

    '''
    
    API Endpoint to change a user's password

    '''

    try:
        success_user = change_password(user, password_data, db)
    except Exception as e:
        raise e

    return success_user


@router.post("/delete_user", response_model=None)
async def delete_user_account(password: UserPassword,
                              user: UserReturn = Depends(get_current_active_user),
                              db: Session = Depends(get_db)):

    '''
    
    API Endpoint to delete a user account if the user chooses to do so
    
    '''

    try:
        success = delete_account(password, user, db)
    except Exception as e:
        raise e

    if success:
        return {
            "message": "account deleted successfully."
        }


@router.post("/rate", response_model=None)
async def test_rate():

    return {
        "message": "pinged."
    }
