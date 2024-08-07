from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    admin_ids: str
    chanel_id: int
    support: str



@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'),
                               admin_ids=env('ADMIN_IDS'),
                               chanel_id=env('CHANEL_ID'),
                               support=env('SUPPORT')))
