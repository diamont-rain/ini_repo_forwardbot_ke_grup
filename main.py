import os
import logging
import asyncio
import uvloop

from pyrogram import filters, Client, idle
from contextlib import closing, suppress
from asyncio import sleep, get_event_loop
from dotenv import load_dotenv
from os.path import exists
from os import remove
from uvloop import install
from pyrogram.enums import MessageMediaType
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.errors import (
    ChatAdminRequired,
    FloodWait,
)

uvloop.install()

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging = logging.getLogger(__name__)

load_dotenv()


client = MongoClient(os.getenv("MONGO_URL"))
db = client["SchedulerBot"]

try:
    replaceable = eval(os.getenv("REPLACE"))
except Exception as e:
    logging.error(e)
    logging.error(f"Konfigurasi REPLACE salah {e}")

try:
    chats = eval(os.getenv("CHATS"))
except Exception as e:
    logging.error(e)
    logging.error(f"Konfigurasi CHATS salah {e}")

bot = Client(
    "bot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True,
)
ubot = Client(
    "ubot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    session_string=os.getenv("STRING_SESSION"),
    device_model=os.getenv("DEVICE_MODEL"),
    in_memory=True,
)

target_channels = [int(i) for i in chats]

@ubot.on_message(filters.chat(target_channels) & ~filters.service)
async def listener(_, message: Message):
    get_groups = chats[message.chat.id]
    await steal(message.chat.id, message.id, get_groups)

async def steal(chat_id, message_id, get_groups):
    try:
        message = await ubot.get_messages(chat_id, message_id)
    except Exception as e:
        return logging.error(f"GetMessage: {chat_id}/{message_id}\n{e}")

    try:
        if message.media and message.media not in (
         MessageMediaType.WEB_PAGE_PREVIEW,
         MessageMediaType.STORY,
         MessageMediaType.CONTACT,
         MessageMediaType.LOCATION,
         MessageMediaType.VENUE,
         MessageMediaType.POLL,
         MessageMediaType.DICE,
         MessageMediaType.GAME):
            media = await message.download()
        else:
            media = None
    except Exception as e:
        return logging.error(f"DownloadMedia: {chat_id}/{message_id}\n{e}")

    try:
        msg = message.caption if media else message.text
    except:
        msg = None
    if msg:
        for key in replaceable:
            for word in replaceable[key]:
                msg = msg.replace(word, key)

    custom_buttons = [
        [
            InlineKeyboardButton("ʟ ᴏ ɢ ɪ ɴ | ᴅ ᴀ ꜰ ᴛ ᴀ ʀ", url="https://bio.site/haotogel888.com"),
        ],
    ]
    buttons = message.reply_markup.inline_keyboard + custom_buttons if message.reply_markup else custom_buttons
    for i in get_groups:
        try:
            if media:
                if message.media == MessageMediaType.PHOTO:
                    pin_msg = await bot.send_photo(
                        int(i),
                        photo=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.VIDEO:
                    pin_msg = await bot.send_video(
                        int(i),
                        video=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.VIDEO_NOTE:
                    pin_msg = await bot.send_video_note(
                        int(i),
                        video_note=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.AUDIO:
                    pin_msg = await bot.send_audio(
                        int(i),
                        audio=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.VOICE:
                    pin_msg = await bot.send_voice(
                        int(i),
                        voice=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.ANIMATION:
                    pin_msg = await bot.send_animation(
                        int(i),
                        animation=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                elif message.media == MessageMediaType.STICKER:
                    pin_msg = await bot.send_sticker(
                        int(i),
                        sticker=media,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
                else:
                    pin_msg = await bot.send_document(
                        int(i),
                        document=media,
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        protect_content=True,
                    )
            else:
                pin_msg = await bot.send_message(
                    int(i),
                    msg,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    protect_content=True,
                )

            msg_id = await db.pin.find_one({"_id": pin_msg.chat.id})
            try:
                if msg_id:
                    await bot.unpin_chat_message(
                        chat_id=pin_msg.chat.id,
                        message_id=msg_id["msg_id"],
                    )
            except FloodWait as e:
                await sleep(e.value)
                if msg_id:
                    await bot.unpin_chat_message(
                        chat_id=pin_msg.chat.id,
                        message_id=msg_id["msg_id"],
                    )
            except ChatAdminRequired:
                logging.error(f"I need to be admins on in {i}!")
            except Exception as e:
                return logging.error(f"UnPinMessage: {pin_msg.chat.id}\n{e}")

            try:
                pinned_msg = await pin_msg.pin(disable_notification=True)
                if pinned_msg:
                    await pinned_msg.delete()
            except FloodWait as e:
                await sleep(e.value)
                pinned_msg = await pin_msg.pin(disable_notification=True)
                if pinned_msg:
                    await pinned_msg.delete()
            except ChatAdminRequired:
                logging.error(f"I need to be admins on {i}!")
            except Exception as e:
                return logging.error(f"PinMessage: {i}/{pin_msg.id}\n{e}")

            data = {"msg_id": pin_msg.id}
            await db.pin.update_one({"_id": pin_msg.chat.id}, {"$set": data}, upsert=True)
        except ChatAdminRequired:
            logging.error(f"I need to be admins on {i}!")
        except Exception as e:
            return logging.error(f"#ERROR: {e}")

    if media and os.path.exists(media):
        try:
            os.remove(media)
        except:
            pass


  async def main():
    await bot.start()
    await bot.send_message(-1001113786188, "__**Bot started.**__")
    me = await bot.get_me()
    bot.name = me.first_name
    print(f"Bot started as {bot.name}")
    await ubot.start()
    me = await ubot.get_me()
    ubot.name = me.first_name
    print(f"Userbot started as {ubot.name}")

    async def stop(ubot):
        await super().stop()
        print("Bot stopped.")
    await startup_restart()
    await idle()



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))
