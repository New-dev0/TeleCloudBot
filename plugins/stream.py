from . import make_url, app, humanbytes, database, get_icon
from swibots import *
from database.client import getClient
from utils.file_properties import get_media_from_message
from base64 import b16encode, b16decode


@app.on_callback_query(regexp("pdfview(.*)"))
async def getDetail(ctx: BotContext[CallbackQueryEvent]):
    url = ctx.event.callback_data.split("|", maxsplit=1)[-1]
    # await ctx.event.message.send(f"New Page: {True}")
    await ctx.event.answer(
        callback=AppPage(components=[FileViewer(url)]), new_page=True
    )


@app.on_callback_query(regexp("detail(.*)"))
async def getDetail(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    chat_id, messageId = ctx.event.callback_data.split("|")[1:]
    comps, lays = [], []
    user = str(ctx.event.action_by_id)
    user = database.child(str(user))
    if not user.child("userLogin").get(shallow=True):
        from .login import openLoginPage

        await openLoginPage(ctx)
        return
    #    pdfView = None
    #    print(chat_id, messageId)
    userbot = await getClient(ctx.event.action_by_id)
    try:
        messageInfo = await userbot.get_messages(chat_id, message_ids=int(messageId))
    except Exception as er:
        messageInfo = None
        print(er)
        comps.append(Text(f"*Error: {er}*\nMessage not found!"))
    if messageInfo:
        media = get_media_from_message(messageInfo)
        user = ctx.event.action_by_id
        name = (getattr(media, "file_name", "photo.png") or "").lower()
        thumb = Icon(
            make_url(chat_id, messageId, ctx.event.action_by_id, True)
            if media and media.thumbs
            else get_icon(name)
        )
        #        print(name)
        if messageInfo.video or name.endswith(
            (".mkv", ".mp4", ".webm", ".mpv", ".avi")
        ):
            comps.append(
                VideoPlayer(make_url(chat_id, messageId, user), title=media.file_name)
            )
            comps.append(Text(f"*Size:* {humanbytes(media.file_size)}"))
        elif messageInfo.audio or name.endswith((".mp3", ".flac", ".ogg", ".m4a")):
            comps.append(
                AudioPlayer(
                    media.file_name,
                    make_url(chat_id, messageId, user),
                    thumb=Image(
                        make_url(chat_id, messageId, ctx.event.action_by_id, True)
                        if media and media.thumbs
                        else "https://ouch-cdn2.icons8.com/0HjMOVLvzi8sGCKqTMicVwySbgSU5As-AEGO4Cj7Ofg/rs:fit:368:284/czM6Ly9pY29uczgu/b3VjaC1wcm9kLmFz/c2V0cy9wbmcvNjAz/LzNiNDAwOWIxLWM0/ZjctNDc5ZS04NTAw/LWRhYzM5YWYyNTQy/Yi5wbmc.png"
                    ),
                )
            )
            comps.append(Text(f"*Size:* {humanbytes(media.file_size)}"))
        elif messageInfo.photo or name.endswith((".jpg", ".png", ".jpeg")):
            comps.append(Image(make_url(chat_id, messageId, user)))
            comps.append(Text(f"*Size:* {humanbytes(media.file_size)}"))
        else:
            lays.append(
                ListView(
                    [
                        ListTile(
                            media.file_name,
                            thumb=thumb,
                            description=f"Size: {humanbytes(media.file_size)}",
                        )
                    ],
                    ListViewType.LARGE,
                )
            )
        if messageInfo.caption or messageInfo.text:
            comps.append(Text(f"*{messageInfo.caption or messageInfo.text}*"))
        if name.endswith((".pdf")):
            comps.append(
                Button(
                    "Open PDF",
                    callback_data=f"pdfview|{make_url(chat, messageId, user)}",
                )
            )
        comps.append(
            ButtonGroup(
                [
                    Button(
                        "Favorite",
                        callback_data=f"filesave|Favorites|{chat_id}|{messageId}",
                        #      color="#7e6fa1",
                    ),
                    Button(
                        "Save file",
                        callback_data=f"opensave|{chat_id}|{messageId}",
                        #     color="#7e6fa1",
                    ),
                    Button(
                        "Share",
                        url=f"https://iswitch.click/telecloud_bot?share={b16encode(f'{chat_id}|{messageId}'.encode()).decode()}",
                    ),
                ]
            )
        )
        comps.append(
            Button(
                "Download",
                url=make_url(chat_id, messageId, user),
                action="download",
                downloadFileName=name,
            )
        )
        addHistory(ctx.event.action_by_id, chat_id, messageId, media)
    callback = AppPage(components=comps, layouts=lays)
    #    print(callback.to_json())
    # await ctx.event.message.send(f"New Page: {True}")
    await ctx.event.answer(callback=callback, new_page=True)


@app.on_command("share")
async def onShare(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    param = ctx.event.params
    if not param:
        return await m.send(f"Provide share hash!")
    try:
        dcoded = b16decode(param).decode().split("|")
        chatId = dcoded[0]
        messageId = dcoded[1]
    except Exception as er:
        print(er)
        return
    try:
        chatId = int(chatId)
    except Exception as er:
        pass
    await m.reply_text(
        f"Click below button to stream file!",
        inline_markup=InlineMarkup(
            [
                [
                    InlineKeyboardButton(
                        "View file", callback_data=f"detail|{chatId}|{messageId}"
                    )
                ]
            ]
        ),
    )


def addHistory(user, chat, messageId, media):
    user = str(user)
    data = {
        "name": getattr(media, "file_name", "photo.png"),
        "chat": chat,
        "msg": messageId,
        "thumb": bool(media.thumbs),
        "size": media.file_size,
    }
    ref = database.child(user).child("history")
    stored = ref.get() or []
    if data in stored:
        stored.remove(data)
    stored.append(data)
    ref.set(stored)
