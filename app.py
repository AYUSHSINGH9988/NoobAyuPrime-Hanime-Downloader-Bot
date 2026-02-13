
import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

# Configuration from Environment Variables
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8354139629:AAFXeLAl1kui4rdlMtKJkONHYlFttBDfh6w")

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def progress_bar(current, total, message, ud_type):
    now = time.time()
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
    
    if now - progress_bar.last_update > 4:
        percentage = current * 100 / total
        elapsed_time = now - progress_bar.start_time
        speed = current / elapsed_time if elapsed_time > 0 else 0
        
        progress_str = (
            f"⚡️ **{ud_type}**\n"
            f"📊 **Progress:** {percentage:.2f}%\n"
            f"🚀 **Speed:** {speed/1024:.2f} KB/s\n"
            f"📁 **Size:** {current/(1024*1024):.2f} MB / {total/(1024*1024):.2f} MB"
        )
        try:
            await message.edit_text(progress_str)
        except:
            pass
        progress_bar.last_update = now

def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **Hello!**\nSend me a Hanime link to download the video. 🤖🚀")

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(client, message: Message):
    url = message.text
    if "hanime.tv" not in url:
        await message.reply_text("❌ **Invalid Link!** Only Hanime.tv links are supported.")
        return

    status_msg = await message.reply_text("🔎 **Processing Link...** ⏳")

    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        progress_bar.start_time = time.time()
        await status_msg.edit_text("📥 **Downloading started...** 🚀")
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        await status_msg.edit_text("📤 **Upload started to Telegram...** ⚡️")
        
        await message.reply_video(
            video=file_path,
            caption=f"✅ **Downloaded:** `{os.path.basename(file_path)}`",
            progress=progress_bar,
            progress_args=(status_msg, "Uploading... 📤")
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:**\n`{str(e)}`")

if __name__ == "__main__":
    print("🔥 Bot is live!")
    app.run()
    
