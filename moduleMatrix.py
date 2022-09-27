# https://matrix-org.github.io/matrix-python-sdk/matrix_client.html
# https://github.com/matrix-org/matrix-python-sdk

# https://matrix-nio.readthedocs.io/en/latest/#api-documentation

import asyncio
import configparser
import sys
import time
from importlib import util

from nio import AsyncClient, RoomMessageText, SyncResponse


async def main():
    async_client = AsyncClient( "https://matrix.org", 
                                "@reflexioneseir:matrix.org")

    response = await async_client.login("bezdma2rfl") 
    print(response)

    await async_client.room_send(
        # Watch out! If you join an old room you'll see lots of old messages
        room_id="!gtvHHqMIfzLLUCoIAd:matrix.org",
        message_type="m.room.message",
        content = {
            "msgtype": "m.text",
            "body": "¡Prueba!"
        }
    )

    return 

    sync_response = await async_client.sync(30000)
    time.sleep(10)

    joins = sync_response.rooms.join

    for room_id in joins:
        print(f"Room id: {room_id}")
        print(joins[room_id])

    print(joins)


if __name__ == '__main__': 
    asyncio.get_event_loop().run_until_complete(main())
