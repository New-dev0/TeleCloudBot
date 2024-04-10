from . import app, getBottomBar, database
from swibots import *
from config import Config
from pyrogram.storage.memory_storage import MemoryStorage
from pyrogram.client import Client
from database.client import getClient
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    AuthKeyUnregistered,
)

Conf = {}


@app.on_callback_query(regexp("inpt"))
async def getUserInfo(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    key = ctx.event.callback_data.split("+")[-1]
    if not Conf.get(user):
        Conf[user] = {}
    Conf[user][key] = ctx.event.details.input_value


@app.on_callback_query(regexp("userlog$"))
async def openLoginPage(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    comps, lays = [], []
    comps.append(Text("Please login with your telegram account to use this bot!"))
    #    comps.append(
    #       TextInput("API ID", placeholder="Optional", callback_data=f"inpt+apiid")
    #  )
    #  comps.append(
    #     TextInput("API HASH", placeholder="Optional", callback_data=f"inpt+apihash")
    # )
    comps.append(Text("Add +countryCode to phone", TextSize.SMALL))
    comps.append(
        TextInput(
            "Phone No", placeholder="Enter Phone Number", callback_data=f"inpt+phoneno"
        )
    )
    # comps.append(
    #     TextInput(
    #         "Bot Token", placeholder="Enter Bot token", callback_data=f"inpt+bottoken"
    #     )
    # )
    comps.append(
        Button(
            "Continue",
            callback_data="sendcode",  #  color="#7e6fa1"
        )
    )
    await ctx.event.answer(callback=AppPage(components=comps, layouts=lays))


@app.on_callback_query(regexp("Profile$"))
async def getInfo(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.callback_data
    user = ctx.event.action_by_id
    if Conf.get(user):
        del Conf[user]
    comps, lays = [], []
    userbot = await getClient(user)
    try:
        me = await userbot.get_me()
    except AuthKeyUnregistered:
        await ctx.event.answer(
            "Your session is expired!\nLogin again...", show_alert=True
        )
        database.child(f"{user}/userLogin").delete()

        from plugins.basic import createHomePage

        await createHomePage(ctx)
        return
    except ConnectionError:
        try:
            await userbot.start()
            me = await userbot.get_me()
        except Exception as er:
            return await ctx.event.answer(f"Error: {er}", show_alert=True)
    except Exception as er:
        return await ctx.event.answer(f"Error: {er}", show_alert=True)
    thumb = None
    if me.username:
        from plugins.channel import getChannelInfo

        info = await getChannelInfo(me.username)
        thumb = info.get("image")

    #    comps.append(Text("Bot Login", TextSize.SMALL))
    #   comps.append(TextInput("Bot Token", value="", callback_data="btoken"))
    comps.append(Text("User Login", TextSize.SMALL))
    if thumb:
        comps.append(Image(thumb))
    comps.append(Text(f"{me.first_name} {me.last_name}".strip(), TextSize.SMALL))
    comps.append(Button("Logout", color="000000", callback_data="logout"))
    #   comps.append(Button(f"Login as User", callback_data="userlog"))
    await ctx.event.answer(
        callback=AppPage(
            components=comps, layouts=lays, bottom_bar=getBottomBar("Profile")
        )
    )


@app.on_callback_query(regexp("logout$"))
async def getInfo(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.callback_data
    user = ctx.event.action_by_id
    #    comps, lays = [], []
    client: Client = await getClient(user)
    await client.log_out()
    await ctx.event.answer("Logged Out!", show_alert=True)

    from plugins.basic import createHomePage

    await createHomePage(ctx)


@app.on_callback_query(regexp("sendcode$"))
async def getUserInfo(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    await asyncio.sleep(1.8)
    data = Conf[user]
    phone_number = data.get("phoneno")
    #    print(data)

    Conf[user]["client"] = client = Client(
        ":memory:",
        api_id=data.get("apiid") or Config.API_ID,
        api_hash=data.get("apihash") or Config.API_HASH,
        in_memory=True,
    )
    #    print(data,)
    await client.connect()
    try:
        code = await client.send_code(phone_number)
    except ApiIdInvalid as er:
        return await ctx.event.answer(f"{er}", show_alert=True)
    except PhoneNumberInvalid as er:
        return await ctx.event.answer(f"{er}", show_alert=True)
    comps, lays = [], []
    comps.append(
        Text(f"A Login code has been send on your *Telegram App*.\nEnter that below!")
    )
    comps.append(TextInput("Enter Login Code", callback_data=f"inpt+code"))
    comps.append(
        Button(
            "Continue",
            callback_data=f"entercode|{code.phone_code_hash}",
            #      color="#7e6fa1",
        )
    )
    await ctx.event.answer(callback=AppPage(components=comps, layouts=lays))


@app.on_callback_query(regexp("entercode"))
async def getUserInfo(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    await asyncio.sleep(1.8)
    hash = ctx.event.callback_data.split("|")[-1]
    if not Conf.get(user):
        return await ctx.event.answer("Something went wrong", show_alert=True)
    data = Conf[user]
    code = Conf[user].get("code")
    comps, lays = [], []
    if not code:
        return await ctx.event.answer("Enter code to login", show_alert=True)
    client: Client = Conf[user]["client"]
    try:
        await client.sign_in(data["phoneno"], hash, code)
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await ctx.event.answer(
            "OTP is invalid. Please start generating session again.", show_alert=True
        )
        return
    except SessionPasswordNeeded:
        comps.append(Text("Enter Password"))
        comps.append(TextInput("Password", callback_data="inpt+password"))
        comps.append(
            Button(
                "Continue",
                callback_data="loginpass",  #  color="#7e6fa1"
            )
        )
        await ctx.event.answer(callback=AppPage(components=comps, layouts=lays))
        return
    string_session = await client.export_session_string()
    #     await client.stop()
    del Conf[user]
    database.child(f"{user}/apiId").set(client.api_id)
    database.child(f"{user}/apiHash").set(client.api_hash)
    database.child(f"{user}/userLogin").set(string_session)

    from plugins.basic import createHomePage

    await createHomePage(ctx)


@app.on_callback_query(regexp("loginpass"))
async def getUserInfo(ctx: BotContext[CallbackQueryEvent]):
    user = ctx.event.action_by_id
    if not Conf.get(user):
        return await ctx.event.answer("Something went wrong", show_alert=True)
    data = Conf[user]
    await asyncio.sleep(1)
    pws = data.get("password")
    if not pws:
        return await ctx.event.answer("Enter password to continue", show_alert=True)
    client: Client = data["client"]
    try:
        await client.check_password(password=pws)
    except PasswordHashInvalid:
        await ctx.event.answer(
            f"Provided password is invalid! Generate again..", show_alert=True
        )
        return
    string_session = await client.export_session_string()
    del Conf[user]

    database.child(f"{user}/apiId").set(client.api_id)
    database.child(f"{user}/apiHash").set(client.api_hash)
    database.child(f"{user}/userLogin").set(string_session)
    #    print(string_session)

    from plugins.basic import createHomePage

    await createHomePage(ctx)
