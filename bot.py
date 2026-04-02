import sys
import glob
import importlib.util
import logging
import logging.config
import asyncio
import uvloop
import time
import pytz
from pathlib import Path
from datetime import date, datetime
from aiohttp import web
from PIL import Image

# --- STEP 1: Loop Policy Setup (Must be before Client imports) ---
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# --- STEP 2: Kurigram Imports (Replacing Pyrogram/Hydrogram) ---
from pyrogram import Client, idle, __version__
from kurigram.raw.all import layer
from kurigram.errors import FloodWait
import kurigram.utils

# Database & Config Imports
from database.ia_filterdb import Media, Media2
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server, check_expired_premium, keep_alive
from dreamxbotz.Bot import dreamxbotz
from dreamxbotz.util.keepalive import ping_server
from dreamxbotz.Bot.clients import initialize_clients

# Image Pixel Limit
Image.MAX_IMAGE_PIXELS = 500_000_000

# Logging Configuration
logging.config.fileConfig('logging.conf')
logging.getLogger("kurigram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pymongo").setLevel(logging.WARNING)

botStartTime = time.time()
kurigram.utils.MIN_CHANNEL_ID = -1009147483647

async def dreamxbotz_start():
    print('\n🚀 Initializing DreamxBotz on Kurigram...')
    await dreamxbotz.start()
    
    bot_info = await dreamxbotz.get_me()
    dreamxbotz.username = "@" + bot_info.username
    
    await initialize_clients()
    
    # Plugin Loader Logic
    ppath = "plugins/*.py"
    files = glob.glob(ppath)
    for name in files:
        plugin_name = Path(name).stem
        import_path = f"plugins.{plugin_name}"
        try:
            spec = importlib.util.spec_from_file_location(import_path, name)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules[import_path] = load
            print(f"DreamxBotz Imported => {plugin_name}")
        except Exception as e:
            print(f"❌ Plugin Error {plugin_name}: {e}")

    if ON_HEROKU:
        asyncio.create_task(ping_server()) 

    # Database Initialization
    try:
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS, temp.BANNED_CHATS = b_users, b_chats
        await Media.ensure_indexes()
        if MULTIPLE_DB:
            await Media2.ensure_indexes()
    except: pass

    # Bot Metadata
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name
    temp.B_LINK = bot_info.mention
    dreamxbotz.username = '@' + bot_info.username
    
    asyncio.create_task(check_expired_premium(dreamxbotz))
    
    # Restart Log
    tz = pytz.timezone('Asia/Kolkata')
    time_now = datetime.now(tz).strftime("%H:%M:%S %p")
    if LOG_CHANNEL:
        try:
            await dreamxbotz.send_message(
                chat_id=LOG_CHANNEL, 
                text=script.RESTART_TXT.format(temp.B_LINK, date.today(), time_now)
            )
        except: 
            pass

    # Web Server Setup (Render Port Binding)
    try:
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()
    except: pass

    asyncio.create_task(keep_alive())
    print(f"✅ {bot_info.first_name} is LIVE on Kurigram!")
    await idle()
    
if __name__ == '__main__':
    try:
        asyncio.run(dreamxbotz_start())
    except FloodWait as e:
        time.sleep(e.value)
    except KeyboardInterrupt:
        print('Service Stopped Bye 👋')
