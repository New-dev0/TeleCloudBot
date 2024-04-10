from requests_cache import CachedSession

from bs4 import BeautifulSoup
from . import app, getBottomBar, database, add_channel
from swibots import *
from database.client import getClient
from pyrogram.raw.functions.contacts.search import Search

ses = CachedSession("stream", expire_after=180)


async def getChannelInfo(username: str):
    url = f"https://t.me/{username}"
    data = ses.get(url).content
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf8")
    img = soup.find("img", "tgme_page_photo_image")
    desc = ""
    try:
        for fd in soup.find("div", "tgme_page_description").children:
            if not fd.text:
                desc += "\n"
            desc += fd.text
    except Exception:
        pass
    return {
        "image": (
            img.get("src")
            if img
            else "https://img.icons8.com/?size=80&id=WbhbrXaJ1lH5&format=png"
        ),
        "name": soup.find("div", "tgme_page_title").text or "",
        "description": desc,
        "extra": soup.find("div", "tgme_page_extra").text.strip(),
    }


@app.on_callback_query(regexp("chl(.*)"))
async def ChannelInfo(ctx: BotContext[CallbackQueryEvent]):
    """open channel description page"""
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    chat = ctx.event.callback_data.split("|")[-1]
    await viewChannel(chat, ctx)


async def viewChannel(chat, ctx: BotContext[CallbackQueryEvent]):
    comps, lays = [], []
    info = await getChannelInfo(chat)
    if img := info.get("image"):
        comps.append(Image(img))
    comps.append(Text(info["name"], TextSize.SMALL))
    if desc := info.get("description"):
        comps.append(Text(f"*Description:*\n{desc}"))
    comps.append(
        Button(
            "Save Channel",
            callback_data=f"addch|{chat}",
            # color="#7e6fa1"
        )
    )
    comps.append(
        Button(
            "View Files",
            callback_data=f"tab|{chat}|Videos|0|open",  # color="#7e6fa1"
        )
    )
    # await ctx.event.message.send(f"New Page: True")
    await ctx.event.answer(
        callback=AppPage(components=comps, layouts=lays), new_page=True
    )


# Search Telegram Chat
@app.on_callback_query(regexp("shtg"))
async def search(ctx: BotContext[CallbackQueryEvent]):
    """search telegram chats"""
    query = ctx.event.details.search_query
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    comps, lays = [], []
    comps.append(SearchBar("Search Chats", callback_data="shtg"))
    if query:
        await ctx.event.answer(
            callback=AppPage(components=[Text(f"Searching for {query}....")])
        )
        userbot = await getClient(ctx.event.action_by_id)
        res = await userbot.invoke(Search(q=query, limit=7))
        listi = []

        async def __get_chat(chat):
            if not chat.username:
                listi.append()
                return
            info = await getChannelInfo(chat.username)
            listi.append(
                ListTile(
                    title=chat.title,
                    description=f"@{chat.username}",
                    thumb=info.get("image")
                    or "https://img.icons8.com/?size=80&id=WbhbrXaJ1lH5&format=png",
                    callback_data=f"chl|{chat.username or chat.id}",
                )
            )

        await asyncio.gather(*[__get_chat(chat) for chat in res.chats if chat.username])

        lays.append(ListView(listi))
    # await ctx.event.message.send(f"New Page: {not query}")
    await ctx.event.answer(
        callback=AppPage(components=comps, layouts=lays), new_page=not query
    )


# TODO: Add all channels using getDialogs


@app.on_callback_query(regexp("Channels"))
async def addChannel(ctx: BotContext[CallbackQueryEvent]):
    """open Channels page in bottom sheet"""
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    listi = []
    comps, lays = [], []
    user = ctx.event.action_by_id

    async def __listItem(chat_id, data):
        from plugins.channel import getChannelInfo

        info = await getChannelInfo(data["username"])
        chat = data.get("username", chat_id)
        listi.append(
            ListTile(
                data["name"],
                description=chat,
                thumb=info.get("image")
                or "https://img.icons8.com/?size=80&id=WbhbrXaJ1lH5&format=png",
                callback_data=f"tab|{chat}|Videos|0|open",
            )
        )

    ref = database.child(str(user)).child("channels").get() or {}
    if ref:
        print(ref)
        await asyncio.gather(
            *[__listItem(chat_id, data) for chat_id, data in ref.items()]
        )
        if listi:
            lays.append(ListView(listi, ListViewType.DEFAULT))
        comps.append(Text("Added Channels:", TextSize.SMALL))
    else:
        comps.append(Text("You have not added any channel!", TextSize.SMALL))
    await ctx.event.answer(
        callback=AppPage(
            components=comps, layouts=lays, bottom_bar=getBottomBar("Channels")
        )
    )


@app.on_callback_query(regexp("addch"))
async def addChannel(ctx: BotContext[CallbackQueryEvent]):
    """add channel from text input"""
    #   print("received", ctx.event.query_id, ctx.event.details.parent_id)

    value = ctx.event.details.input_value
    if "|" in ctx.event.callback_data:
        value = ctx.event.callback_data.split("|")[-1]
    user = ctx.event.action_by_id
    if not value:
        await ctx.event.answer("Please enter channel username", show_alert=True)
        return
    await add_channel(value, user)
    await ctx.event.answer("Added Channel!", show_alert=True)
