# Taken from megadlbot_oss <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/webserver/routes.py>
# Thanks to Eyaadh <https://github.com/eyaadh>

import re
import time, asyncio
import math
import logging
import secrets, utils
import mimetypes
from typing import Union
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from config import Config as Var
from telegram import tgbot
from database.client import getClient
from streamer.exceptions import *
from client import work_loads

logger = logging.getLogger("routes")
StartTime = time.time()

routes = web.RouteTableDef()


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response(
        {
            "server_status": "running",
            "uptime": utils.get_readable_time(time.time() - StartTime),
            "loads": dict(
                ("bot" + str(c + 1), l)
                for c, (_, l) in enumerate(
                    sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
                )
            ),
        }
    )


@routes.get(r"/stream", allow_head=True)
async def stream_handler(request: web.Request):
    return await __stream_handler(request)


@routes.get(r"/thumb", allow_head=True)
async def stream_handler(request: web.Request):
    return await __stream_handler(request, True)


async def __stream_handler(request: web.Request, thumb=False):
    try:
        channel = request.query.get("channel")
        messageId = int(request.query.get("messageId"))
        user = int(request.query.get("userId"))
        return await media_streamer(request, channel, messageId, thumb, user)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


class_cache = {}


async def media_streamer(
    request: web.Request,
    channel: Union[str, int],
    message_id: int,
    thumb: bool = False,
    userid: int = 0,
):
    range_header = request.headers.get("Range", 0)

    index = min(work_loads, key=work_loads.get)
    if not class_cache.get(0):
        class_cache[0] = utils.ByteStreamer(tgbot)

    try:
        msg = await tgbot.get_messages(channel, message_ids=message_id)
        assert msg != None
        faster_client = tgbot
        tg_connect = class_cache[0]
    except Exception as er:
        logger.info(f"check tgbot access: {er}")
        faster_client = await getClient(userid)  # multi_clients[index]

        #    if Var.MULTI_CLIENT:
        #        logger.info(f"Client {index} is now serving {request.remote}")

        if class_cache.get(userid):
            tg_connect = class_cache[userid]
            logger.debug(f"Using cached ByteStreamer object for client {userid}")
        else:
            logger.debug(f"Creating new ByteStreamer object for client {userid}")
            tg_connect = utils.ByteStreamer(faster_client)
            class_cache[userid] = tg_connect

    logger.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(channel, message_id, thumb)
    #    print(file_id, thumb)
    logger.debug("after calling get_file_properties")

    #    if utils.get_hash(file_id.unique_id, 7) != secure_hash:
    #       logger.debug(f"Invalid hash for message with ID {message_id}")
    #      raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )
    mime_type = file_id.mime_type
    file_name = utils.get_name(file_id)
    print(file_name, mime_type, file_id)
    disposition = "attachment"

    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    if "video/" in mime_type or "audio/" in mime_type or "/html" in mime_type:
        disposition = "inline"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": str(mime_type),
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
    )
