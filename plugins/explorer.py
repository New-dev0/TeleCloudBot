from swibots import (
    AppPage,
    ListView,
    ListTile,
    Image,
    Button,
    Spacer,
    ButtonGroup,
    TextSize,
    ListViewType,
    regexp,
    BotContext,
    CallbackQueryEvent,
    Grid,
    Text,
    AppBar,
    SearchBar,
    GridItem,
    SearchHolder,
    TabBar,
    TabBarTile,
)
from . import app, make_url, humanbytes, get_icon
from pyrogram.enums.messages_filter import MessagesFilter
from pyrogram.types import Message
from plugins.channel import getChannelInfo
from database.client import getClient

TABS = {
    "Videos": {"filter": MessagesFilter.VIDEO, "attr": "video"},
    "  Files  ": {"filter": MessagesFilter.DOCUMENT, "attr": "document"},
    " Audio ": {"filter": MessagesFilter.AUDIO, "attr": "audio"},
    "Images": {"filter": MessagesFilter.PHOTO, "attr": "photo"},
    " GIFs ": {"filter": MessagesFilter.ANIMATION, "attr": "animation"},
    #    "Links": {"filter": MessagesFilter.URL},
}
LIMIT = 20


async def makeSearchTABS(user, chat: str, selected="Images", offset=0):
    comps, lays = [], []
    tabtiles = []
    for tab in TABS.keys():
        tabtiles.append(
            TabBarTile(
                tab, callback_data=f"tab|{chat}|{tab}|0", selected=tab == selected
            )
        )
    comps.append(TabBar(tabtiles))
    #    if selected != "Images":
    #       comps.append(SearchHolder(f"Search...", callback_data=f"srch|{selected}|{chat}"))

    bts = []
    if offset:
        bts.append(
            Button(
                "Previous",
                callback_data=f"tab|{chat}|{selected}|{offset-1}",
                #   color="#7e6fa1",
            )
        )
    if not TABS.get(selected):
        return
    private = False
    title = None
    cThumb = None
    try:
        chat = int(chat)
        private = True
    except Exception:
        chInfo = await getChannelInfo(chat)
        cThumb = chInfo.get("image")
        title = chInfo["name"]
    # for document or audio
    userbot = await getClient(user)

    listitem = []
    data = TABS[selected]
    filter, attr = data["filter"], data.get("attr")
    count = await userbot.search_messages_count(chat, filter=filter)
    results = 0
    message = None
    async for message in userbot.search_messages(
        chat, filter=filter, limit=LIMIT, offset=offset * LIMIT
    ):
        results += 1
        message: Message
        media = getattr(message, attr, None)
        if not media:
            continue
        if selected.strip() in ["GIFs", "Images"]:
            listitem.append(
                GridItem(
                    "",
                    media=make_url(
                        chat, message.id, user, bool(selected.strip() == "GIFs")
                    ),
                    callback_data=f"detail|{chat}|{message.id}",
                )
            )
        else:
            listitem.append(
                ListTile(
                    title=media.file_name,
                    thumb=(
                        make_url(chat, message.id, user, True)
                        if media.thumbs
                        else get_icon(media.file_name)
                    ),
                    description=f"Size: {humanbytes(media.file_size)}",
                    callback_data=f"detail|{chat}|{message.id}",
                )
            )
    page__count = results if not offset else (offset * LIMIT) + results
    if page__count < count and not (offset == 0 and results < LIMIT):
        bts.append(
            Button(
                "Next",
                callback_data=f"tab|{chat}|{selected}|{offset+1}",
                #                color="#7e6fa1",
            )
        )
    comps.append(ButtonGroup(bts))
    if listitem:
        if selected.strip() not in ["Images", "GIFs"]:
            lays.append(ListView(listitem))
        else:
            lays.append(Grid(options=listitem))
    else:
        comps.append(Text(f"No {selected} found!"))
        comps.append(Spacer(y=80))
        comps.append(
            Image(
                "https://f004.backblazeb2.com/file/switch-bucket/6521f53c-c45d-11ee-849e-a4b7a49d7fec.png"
            )
        )
    if results:
        comps.insert(
            1, SearchHolder(f"Search...", callback_data=f"srch|{selected}|{chat}")
        )
    return AppPage(
        components=comps,
        layouts=lays,
        app_bar=AppBar(
            title=title[:15] or (message.chat.title[:15] if message else None),
            left_icon=cThumb
            or "https://f004.backblazeb2.com/file/switch-bucket/b56ec7a0-c44f-11ee-9cb5-a4b7a49d7fec.png",
        ),
    )


@app.on_callback_query(regexp("tab(.*)"))
async def getTab(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    data = ctx.event.callback_data.split("|")
    chat_id = data[1]
    tabId = data[2]
    offset = int(data[3])
    try:
        open = bool(data[4])
        # if open:
        #     await ctx.event.answer(
        #         callback=AppPage(
        #             components=[
        #                 Image(
        #                     "https://i.giphy.com/xTk9ZvMnbIiIew7IpW.webp",
        #                     dark_url="https://i.giphy.com/4EFt4UAegpqTy3nVce.webp",
        #                 ),
        #                 Text("Fetching Info..", TextSize.SMALL),
        #             ]
        #         ),
        #         new_page=True
        #     )
    except:
        open = False
    # await ctx.event.message.send(f"New Page: {open}")

    await ctx.event.answer(
        callback=await makeSearchTABS(ctx.event.action_by_id, chat_id, tabId, offset),
        new_page=open,
    )


@app.on_callback_query(regexp("srch(.*)"))
async def getTab(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")
    category, chat = ctx.event.callback_data.split("|")[1:]
    comps, lays = [], []
    query = ctx.event.details.search_query
    comps.append(
        SearchBar(f"Search {category}..", callback_data=ctx.event.callback_data)
    )
    if query:
        await ctx.event.answer(
            callback=AppPage(
                components=[
                    SearchBar(
                        f"Search {category}..", callback_data=ctx.event.callback_data
                    ),
                    Text(f"Searching for {query}...."),
                ]
            )
        )
        filter = TABS[category]["filter"]
        attr = TABS[category]["attr"]
        listitem = []
        userbot = await getClient(ctx.event.action_by_id)
        async for message in userbot.search_messages(
            chat, filter=filter, limit=LIMIT, query=query
        ):
            message: Message
            media = getattr(message, attr, None)
            if not media:
                continue
            listitem.append(
                ListTile(
                    title=media.file_name,
                    thumb=(
                        make_url(chat, message.id, ctx.event.action_by_id, True)
                        if media.thumbs
                        else get_icon(media.file_name)
                    ),
                    description=f"Size: {humanbytes(media.file_size)}",
                    callback_data=f"detail|{chat}|{message.id}",
                )
            )
        if listitem:
            lays.append(ListView(listitem))
        else:
            comps.append(Text(f"No Results found!"))
    # await ctx.event.message.send(f"New Page: {not query}")

    await ctx.event.answer(
        callback=AppPage(components=comps, layouts=lays), new_page=not query
    )
