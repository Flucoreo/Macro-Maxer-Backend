from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    '''
    Basic config for the api
    '''

    origins: str = Field(
        default="http://localhost:3000",
        title="Origins",
        description="The origins of the API."
    )

settings = Settings()

def get_settings() -> Settings:
    '''
    return our default settings
    '''

    return settings
