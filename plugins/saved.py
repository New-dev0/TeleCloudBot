from . import add_channel, database, app, getBottomBar, make_url, get_icon, humanbytes
from swibots import *
from utils.file_properties import get_media_from_message
from database.client import getClient
from base64 import b16decode, b16encode

DEFAULT = {
    a: {"__type": "folder"}
    for a in ["Videos", "Photos", "Documents", "Audios", "Favorites"]
}

Colf = {}


@app.on_callback_query(regexp("adfolder"))
async def viewSaved(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")
    user = ctx.event.action_by_id
    if not Colf.get(user):
        await ctx.event.answer("Enter folder name", show_alert=True)
        return
    folname = Colf[user]
    call = ctx.event.callback_data.split("|")[-1].strip()
    ref = database.child(str(user)).child("folder")
    if call:
        ref = ref.child(call)
    if "|" in folname or "/" in folname:
        return await ctx.event.answer(
            "Folder name can't contain special characters!", show_alert=True
        )
    ref.child(folname).child("__type").set("folder")
    await ctx.event.answer("Created folder", show_alert=True)


@app.on_callback_query(regexp("folm"))
async def viewSaved(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    Colf[user] = ctx.event.details.input_value


@app.on_callback_query(regexp("Saved"))
async def viewSaved(ctx: BotContext[CallbackQueryEvent]):
    """Open save page"""
    data = ctx.event.callback_data
    count = data.count("|")
    #    print(data.split("|"), count)
    await createFolderView(ctx)


@app.on_callback_query(regexp("opensave"))
async def viewSaved(ctx: BotContext[CallbackQueryEvent]):
    data = ctx.event.callback_data.split("|")[1:]
    if len(data) == 2:
        await createFolderView(ctx, save=True, msg_id=data[-1], chat=data[0])
    else:
        await createFolderView(
            ctx, save=True, msg_id=data[1], chat=data[0], query=data[2]
        )


Icons = {
    "Favorites": "https://img.icons8.com/?size=64&id=52996&format=png&color=1A6DFF,C822FF",
    "Audios": "https://img.icons8.com/?size=64&id=49455&format=png&color=1A6DFF,C822FF",
    "Videos": "https://img.icons8.com/?size=64&id=43625&format=png&color=1A6DFF,C822FF",
    "Photos": "https://img.icons8.com/?size=64&id=iQw1vvRXCjAh&format=png&color=1A6DFF,C822FF",
    "Documents": "https://img.icons8.com/?size=64&id=DreFgCmZrddj&format=png&color=1A6DFF,C822FF",
}


async def createFolderView(
    ctx: BotContext[CallbackQueryEvent],
    save: bool = False,
    msg_id: int = None,
    chat=None,
    query="",
):
    user = str(ctx.event.action_by_id)
    if Colf.get(ctx.event.action_by_id):
        del Colf[ctx.event.action_by_id]
    comps, lays = [], []
    ref = database.child(user).child("folder")

    if not save and "|" in ctx.event.callback_data:
        query = ctx.event.callback_data.split("|")[-1]
        ref = ref.child(query)
    elif query:
        if query.startswith("/"):
            query = query[1:]
        ref = ref.child(query)
    keys = ref.get()
    shared = False
    #    print(keys, ref, query)
    if keys.get("__user"):
        shared = True
        user = keys["__user"]
        ref = database.child(keys["__user"]).child("folder").child(query)
        keys = ref.get()
    if save:
        comps.append(Text("Choose folder path!"))
        comps.append(
            Button(
                "Save file",
                callback_data=f"filesave|{query}|{user}|{chat}|{msg_id}",  # color="#7e6fa1"
            )
        )
    else:
        comps.append(TextInput("Enter folder name", callback_data="folm"))
        #    print(query)
        comps.append(
            ButtonGroup(
                [
                    Button(
                        f"Add {'Sub' if query else ''}Folder",
                        callback_data=f"adfolder|{query}",
                        #                 color="#7e6fa1"
                    ),
                    Button(
                        "Share folder",
                        url=f"https://iswitch.click/telecloud_bot?folder={b16encode(f'{query}|{user}'.encode()).decode()}",
                        clipboard=True,
                    ),
                ]
            )
        )
    if query:
        comps.append(Text(f"*Folder:* {query}", TextSize.SMALL))
    if not keys:
        ref.set(DEFAULT)
        keys = DEFAULT
    listim = []
    for d, v in keys.items():
        if d == "__type":
            continue
        print(d, v, type(v))
        file = v.get("msg")
        title = d
        count = len(v.keys()) - 1
        thumb = None
        if save:
            qm = f"opensave|{chat}|{msg_id}|{query}/{d}"
        else:
            if not file:
                thumb = Icons.get(d)
            if file:
                chat = v["chat"]
                msg = v["msg"]
                title = v["name"]
                qm = f"detail|{chat}|{msg}"
                if v["thumb"]:
                    thumb = make_url(chat, msg, ctx.event.action_by_id, True)
            elif query:
                qm = f"Saved|{query}/{d}"
            else:
                qm = f"Saved|{d}"
            if not thumb and not file:
                thumb = get_icon("folder")
        listim.append(
            ListTile(
                title,
                description=(
                    (f"Shared folder by {user}" if shared else f"{count} Folders")
                    if not file
                    else f"File size: {humanbytes(v.get('size', 0))}"
                ),
                callback_data=qm,
                thumb=thumb or get_icon(title),
            )
        )
    if listim:
        lays.append(ListView(listim, ListViewType.DEFAULT))
    await ctx.event.answer(
        callback=AppPage(
            components=comps, layouts=lays, bottom_bar=getBottomBar("Saved")
        ),
        new_page=save,
    )


@app.on_command("folder")
async def onShare(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    param = ctx.event.params
    if not param:
        return await m.send(f"Provide folder hash!")
    try:
        dcoded = b16decode(param).decode().split("|")
        path = dcoded[0]
        query = dcoded[1]
    except Exception as er:
        print(er)
        return
    if int(query) == m.user.id:
        return await m.send("You can't share your folder!")
    database.child(str(m.user.id)).child("folder").child(path).update({"__user": query})
    await m.reply_text(
        f"Added {path} to Explorer!",
    )


@app.on_callback_query(regexp("filesave"))
async def viewSaved(ctx: BotContext[CallbackQueryEvent]):
    """Save file"""
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    data = ctx.event.callback_data.split("|")[1:]
    #    user = str(ctx.event.action_by_id)
    userbot = await getClient(str(ctx.event.action_by_id))
    query = data[0]
    user = data[1]
    chat = data[2]
    messageId = data[3]
    if query.startswith("/"):
        query = query[1:]
    media = await userbot.get_messages(chat_id=chat, message_ids=int(messageId))
    media = get_media_from_message(media)
    data = {
        "__type": "file",
        "name": getattr(media, "file_name", "photo.png"),
        "chat": chat,
        "msg": messageId,
        "thumb": bool(media.thumbs),
        "size": media.file_size,
    }
    ref = database.child(f"{user}/folder/{query}").child(f"{chat}:{messageId}")
    ref.set(data)
    await ctx.event.answer("Saved!", show_alert=True)
