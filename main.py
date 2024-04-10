import logging, os

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler(filename="telecloud.log")],
)


import asyncio
from aiohttp import web
from client import app
from streamer import web_server
from telegram import tgbot

from config import PORT, BIND_ADDRESS

loop = asyncio.get_event_loop()

server = web.AppRunner(web_server())

if not os.path.isdir("sessions"):
    os.mkdir("sessions")


async def main():
    await server.setup()
    await web.TCPSite(server, BIND_ADDRESS, PORT).start()
    logging.info("Service Started")
    await tgbot.start()


loop.run_until_complete(main())

try:
    app.run()
finally:
    loop.run_until_complete(server.cleanup())
