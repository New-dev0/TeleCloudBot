import asyncio
from client import app
from database import database
from database.client import getClient
import requests

from swibots import (
    CallbackQueryEvent,
    MessageEvent,
    MessageHandler,
    Message,
    BotContext,
    CommandEvent,
    InlineMarkup,
    InlineKeyboardButton,
)
from config import BIND_ADDRESS, PORT
from swibots import *


async def listen(message: Message, timeout: int = 180):
    chat_id = (
        message.user_session_id
        or message.channel_id
        or message.group_id
        or message.user_id
    )
    MESSAGES = []

    async def on_message(m: Message):
        c_id = m.user_session_id or m.channel_id or m.group_id or m.user_id
        if chat_id == c_id:
            MESSAGES.append(message)

    async def getMessages():
        while not MESSAGES:
            await asyncio.sleep(0.002)

    handler = MessageHandler(on_message)

    app.add_handler(handler)
    try:
        await asyncio.wait_for(getMessages(), timeout=timeout)
    except TimeoutError as er:
        raise er
    finally:
        app.remove_handler(handler)
    return MESSAGES[0]


def humanbytes(size):
    if not size:
        return "0 B"
    for unit in ["", "K", "M", "G", "T"]:
        if size < 1024:
            break
        size /= 1024
    if isinstance(size, int):
        size = f"{size}{unit}B"
    elif isinstance(size, float):
        size = f"{size:.2f}{unit}B"
    return size


def make_url(chat_id, message_id, userid: int, thumb: bool = False):
    endpoint = "thumb" if thumb else "stream"
    url = f"http://{BIND_ADDRESS}:{PORT}/{endpoint}?channel={chat_id}&messageId={message_id}&userId={userid}"
    #    print(url)
    return url


def getBottomBar(selected: str = "Home"):
    tiles = []
    bar = {
        "Home": {
            "select": "https://f004.backblazeb2.com/file/switch-bucket/40bb90ed-c428-11ee-abbb-a4b7a49d7fec.png",
            "icon": "https://f004.backblazeb2.com/file/switch-bucket/3ca28d2c-c428-11ee-93e3-a4b7a49d7fec.png",
            "dark": "https://f004.backblazeb2.com/file/switch-bucket/339fa29a-c428-11ee-9c00-a4b7a49d7fec.png",
        },
        "Channels": {
            "icon": "https://f004.backblazeb2.com/file/switch-bucket/44ceb468-c428-11ee-9fba-a4b7a49d7fec.png",
            "dark": "https://f004.backblazeb2.com/file/switch-bucket/494c6263-c428-11ee-b332-a4b7a49d7fec.png",
            "select": "https://f004.backblazeb2.com/file/switch-bucket/3eaf736c-c428-11ee-8896-a4b7a49d7fec.png",
        },
        "Saved": {
            "icon": "https://f004.backblazeb2.com/file/switch-bucket/42df0afc-c428-11ee-8272-a4b7a49d7fec.png",
            "select": "https://f004.backblazeb2.com/file/switch-bucket/35c08cfc-c428-11ee-a703-a4b7a49d7fec.png",
            "dark": "https://f004.backblazeb2.com/file/switch-bucket/30bd7fca-c428-11ee-bdf4-a4b7a49d7fec.png",
        },
        "History": {
            "icon": "https://f004.backblazeb2.com/file/switch-bucket/39fb1d40-c428-11ee-91c8-a4b7a49d7fec.png",
            "select": "https://f004.backblazeb2.com/file/switch-bucket/37d71121-c428-11ee-8f66-a4b7a49d7fec.png",
            "dark": "https://f004.backblazeb2.com/file/switch-bucket/297740bb-c428-11ee-9908-a4b7a49d7fec.png",
        },
        "Profile": {
            "icon": "https://f004.backblazeb2.com/file/switch-bucket/6760e7e7-c42c-11ee-acb2-a4b7a49d7fec.png",
            "select": "https://f004.backblazeb2.com/file/switch-bucket/6c976238-c42c-11ee-92fb-a4b7a49d7fec.png",
            "dark": "https://f004.backblazeb2.com/file/switch-bucket/6a42995a-c42c-11ee-98d0-a4b7a49d7fec.png",
        },
    }
    for opt, keys in bar.items():
        tiles.append(
            BottomBarTile(
                opt,
                callback_data=opt,
                selected=opt == selected,
                icon=keys["icon"],
                dark_icon=keys["dark"],
                selection_icon=keys["select"],
            )
        )
    return BottomBar(
        tiles,  # theme_color="#fcba03"
    )


async def add_channel(value, user):
    userbot = await getClient(user)

    chatInfo = await userbot.get_chat(value)
    ref = database.child(str(user)).child("channels")
    if not ref.child(str(chatInfo.id)).get():
        data = {
            "name": chatInfo.title,
            "username": chatInfo.username,
        }
        ref.child(str(chatInfo.id)).set(data)


def get_extension(path):
    if "." in path:
        return path.split(".")[-1].lower()
    return ""


def get_icon(path):
    if path == "folder":
        return "https://img.icons8.com/?size=64&id=71cUHRMvCNMk&format=png&color=1A6DFF,C822FF"
    ext = get_extension(path)
    if ext:
        url = f"https://img.icons8.com/nolan/64/{ext}.png"
        if requests.get(url).status_code == 200:
            return url
    if ext in ["mp4", "mkv", "mpv", "avi"]:
        return "https://img.icons8.com/?size=64&id=TMIV5nMneLUt&format=png&color=1A6DFF,C822FF"
    elif ext in ["png", "jpeg", "webp"]:
        return "https://img.icons8.com/?size=64&id=iQw1vvRXCjAh&format=png"
    elif ext in ["zip", "rar"]:
        return "https://img.icons8.com/?size=64&id=kyJT2SZUCOb_&format=png&color=1A6DFF,C822FF"
    elif ext in ["iso", "exe"]:
        return "https://img.icons8.com/?size=64&id=52146&format=png&color=1A6DFF,C822FF"
    return "https://img.icons8.com/?size=64&id=44004&format=png&color=1A6DFF,C822FF"
