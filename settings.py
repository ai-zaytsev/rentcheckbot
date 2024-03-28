from environs import Env
from dataclasses import dataclass

@dataclass
class Bots:
    bot_token: str
    api_key: str

@dataclass
class Settings():
    bots: Bots

def get_settings():
    env = Env()
    env.read_env()

    return Settings(
        bots=Bots(
            bot_token = env.str("TOKEN"),
            api_key = env.str("API_KEY")
        )
    )

settings = get_settings()