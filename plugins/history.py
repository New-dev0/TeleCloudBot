from . import app, getBottomBar, database, make_url, get_icon, humanbytes
from swibots import (
    BotContext,
    CallbackQueryEvent,
    regexp,
    AppPage,
    Text,
    TextSize,
    ListTile,
    ListViewType,
    ListView,
)


@app.on_callback_query(regexp("History"))
async def history(ctx: BotContext[CallbackQueryEvent]):
    # await ctx.event.message.send(f"callback: {ctx.event.query_id}\nParent: {ctx.event.details.parent_id}")

    user = str(ctx.event.action_by_id)
    ref = database.child(user).child("history").get() or []
    comps, lays = [], []
    if not ref:
        comps.append(Text("You have not viewed any files!", TextSize.SMALL))
    else:
        comps.append(Text("Recently Viewed:", TextSize.SMALL))

        litem = []
        for liko in ref:
            if liko["thumb"]:
                thumb = make_url(
                    liko["chat"], liko["msg"], ctx.event.action_by_id, True
                )
            else:
                thumb = get_icon(liko["name"])
            litem.append(
                ListTile(
                    liko.get("name"),
                    callback_data=f"detail|{liko['chat']}|{liko['msg']}",
                    description=f"File Size: {humanbytes(liko.get('size', 0))}",
                    thumb=thumb,
                )
            )
        if litem:
            lays.append(ListView(litem, ListViewType.DEFAULT))
    await ctx.event.answer(
        callback=AppPage(
            components=comps, layouts=lays, bottom_bar=getBottomBar("History")
        )
    )
