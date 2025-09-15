import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis

from app.db.database import Base, engine
from app.api import router
from app.config import get_settings

load_dotenv()
redis_host = os.getenv('REDIS_HOST')
redis_port = os.getenv('REDIS_PORT')
redis_password = os.getenv('REDIS_PASSWORD')

app = FastAPI()
Base.metadata.create_all(bind=engine)

# Load application settings from configuration.
SETTINGS = get_settings()

# Add the middleware settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include all API end points
app.include_router(router, prefix="/vb")

@app.on_event("startup")
async def startup_event():
    '''
    Connect to redis on start up
    '''
    app.state.redis = Redis(host=redis_host, port=redis_port, password=redis_password)
    # app.state.redis = Redis(host=redis_host, port=redis_port)

@app.on_event("shutdown")
async def stutdown_event():
    '''
    Disconnect from redis on shut down
    '''
    app.state.redis.close()
