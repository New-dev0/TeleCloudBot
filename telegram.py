import asyncio
from config import Config
from pyrogram import Client

tgbot = Client(
    "bot", bot_token=Config.TG_BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH
)
