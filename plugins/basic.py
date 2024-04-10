import asyncio
from . import *
from database.client import getClient


@app.on_command("start")
async def getStartMessage(ctx: BotContext[CommandEvent]):
    m = ctx.event.message

    await m.reply_text(
        f"Hi *{m.user.name}*",
        inline_markup=InlineMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Open APP",
                        callback_data="Home",
                    ),
                ]
            ]
        ),
    )


Conf = {}


@app.on_callback_query(regexp("chusername"))
async def createHomePage(ctx: BotContext[CallbackQueryEvent]):
    Conf[ctx.event.action_by_id] = ctx.event.details.input_value


CHANNELS = [
    "amazingnatures",
    "Novels_English_Books_Magazines",
    "booksmania",
    "dsabooks",
]


@app.on_callback_query(regexp("Add$"))
async def createHomePage(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")
    username = Conf.get(ctx.event.action_by_id)
    if not username:
        return await ctx.event.answer("Please enter channel username", show_alert=True)

    #    print(username)
    from plugins.channel import viewChannel

    await viewChannel(username, ctx)


@app.on_callback_query(regexp("Home$"))
async def createHomePage(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    comps, lays = [], []
    user = userId = ctx.event.action_by_id
    if Conf.get(user):
        del Conf[user]

    user = database.child(str(user))
    if not user.child("userLogin").get(shallow=True):
        from plugins.login import openLoginPage

        await openLoginPage(ctx)
        return
    asyncio.create_task(getClient(ctx.event.action_by_id))
    comps.append(SearchHolder("Search Channels.", callback_data="shtg"))
    comps.append(TextInput("Enter Channel username", callback_data="chusername"))
    comps.append(
        Button(
            "Add Channel",
            callback_data="Add",  # color="#7e6fa1"
        )
    )

    async def __createGrid(username):
        from plugins.channel import getChannelInfo

        info = await getChannelInfo(username)
        return GridItem(
            info.get("name"), media=info.get("image"), callback_data=f"chl|{username}"
        )

    lays.append(
        Grid(
            title="Recommended",
            horizontal=True,
            options=await asyncio.gather(
                *[__createGrid(username) for username in CHANNELS]
            ),
        )
    )
    # lays.append(
    #     ListView(
    #         options=[ListTile("Favorites", callback_data="Saved")],
    #         view_type=ListViewType.SMALL,
    #     )
    # )
    litem = []
    for liko, data in (user.child("folder").child("Favorites").get() or {}).items():
        if liko == "__type":
            continue
        thumb = None
        if data["thumb"]:
            thumb = make_url(liko["chat"], liko["msg"], userId, True)
        else:
            thumb = get_icon(liko.get("name"))
        litem.append(
            GridItem(
                data.get("name"),
                callback_data=f"detail|{data['chat']}|{data['msg']}",
                media=thumb,
            )
        )
    if litem:
        lays.append(
            Grid(
                title="Favorites",
                options=litem,
                horizontal=True,
                grid_type=GridType.SMALL,
                right_image="https://f004.backblazeb2.com/file/switch-bucket/5954cf6d-c42f-11ee-89f7-a4b7a49d7fec.png",
                image_callback="Saved",
            )
        )
    # lays.append(
    #     ListView(
    #         options=[ListTile("View History", callback_data="History")],
    #         view_type=ListViewType.SMALL,
    #     )
    # )
    litem = []
    for liko in (user.child("history").get() or [])[:-5]:
        if liko["thumb"]:
            thumb = make_url(liko["chat"], liko["msg"], userId, True)
        else:
            thumb = get_icon(liko.get("name"))

        litem.append(
            GridItem(
                liko.get("name"),
                callback_data=f"detail|{liko['chat']}|{liko['msg']}",
                media=thumb,
            )
        )
    if litem:
        lays.append(
            Grid(
                title="History",
                options=litem,
                horizontal=True,
                grid_type=GridType.SMALL,
                right_image="https://f004.backblazeb2.com/file/switch-bucket/5954cf6d-c42f-11ee-89f7-a4b7a49d7fec.png",
                image_callback="History",
            )
        )
    await ctx.event.answer(
        callback=AppPage(components=comps, layouts=lays, bottom_bar=getBottomBar())
    )
