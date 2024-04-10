import logging, asyncio

from database import database
from pyrogram.client import Client
from config import Config
from time import time

TimeHandler = {}
ClientHolder = {}


async def stopClient(user):
    while (client := ClientHolder.get(user)) and TimeHandler.get(user):
        logging.debug(f"checking user:client {user}")
        diff = (time() - TimeHandler[user]) / 60
        # if client is not used for more than 15 minutes
        # disconnect the client
        if diff > 15:
            logging.debug(f"stopping user:client {user}")
            await client.stop()
            del ClientHolder[user]
            del TimeHandler[user]
        await asyncio.sleep(30)


async def getClient(user):
    user = str(user)
    TimeHandler[user] = time()
    if ClientHolder.get(user):
        return ClientHolder[user]
    ref = database.child(user)
    token = ref.child("userLogin").get()
    apiId = ref.child("apiId").get()
    apiHash = ref.child("apiHash").get()

    if not token:
        return
    logging.info(f"Logging as [{user}]")
    client = Client(
        f"sessions/{user}",
        api_id=apiId or Config.API_ID,
        api_hash=apiHash or Config.API_HASH,
        session_string=token,
        app_version=Config.APP_VERSION,
        workers=Config.WORKERS,
        # proxy={
        #     "scheme": "socks5",
        #     "hostname": "172.93.110.144",
        #     "port": 32268
        # }
    )
    ClientHolder[user] = client
    await client.start()
    asyncio.create_task(stopClient(user))
    return client
