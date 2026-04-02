Import logging
import logging.config
import asyncio
import uvloop
from pyrogram import Client
from pyrogram import types
from typing import Union, Optional, AsyncGenerator
from aiohttp import web
from info import *

# --- Logging Setup (Render Fix: Logs ko short rakhne ke liye) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("kurigram").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

# --- Loop Policy Setup ---
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class dreamcinezoneXBot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=60,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """
        Kurigram optimized message iterator.
        Sequentially iterate through chat messages.
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            
            # Fetching messages in chunks for efficiency
            messages = await self.get_messages(
                chat_id, 
                list(range(current, current + new_diff + 1))
            )
            
            for message in messages:
                yield message
                current += 1
      
# Client instance initialize karein
dreamxbotz = dreamcinezoneXBot()

multi_clients = {}
work_loads = {}

# Fix according to pyrogram
