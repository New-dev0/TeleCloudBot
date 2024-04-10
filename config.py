from typing import Any
from decouple import config
from os import environ

PORT = int(environ.get("PORT", 8080))
BIND_ADDRESS = str(config("WEB_SERVER_BIND_ADDRESS", default="0.0.0.0"))
BIN_CHANNEL = str(environ.get("BIN_CHANNEL", ""))


class ConfigHandler:
    BOT_TOKEN: str = config("BOT_TOKEN", default="", cast=str)  # type: ignore
    OWNER_ID: int = config("OWNER_ID", cast=int, default=0)
    FIREBASE_URL: str = config("FIREBASE_URL", default="", cast=str)  # type: ignore
    APP_VERSION: str = config("APP_VERSION", default="0.0.1")
    WORKERS: int = config("WORKERS", cast=int, default=28)

    def __getattr__(self, __name: str) -> Any:
        if __name in self.__dict__:
            return self.__dict__[__name]
        return config(__name, default="")


Config = ConfigHandler()
