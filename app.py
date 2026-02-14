import os
import time
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
import yt_dlp
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8354139629:AAFXeLAl1kui4rdlMtKJkONHYlFttBDfh6w")

# Client Setup
app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DUMMY WEB SERVER (Koyeb Health Check Fix) ---
async def web_handler(request):
    return web.Response(text="Bot is Running on Koyeb!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", web_handler)
    runner = web.AppRunner(server)
    await runner.setup()
    # Koyeb PORT environment variable use karta hai, default 8000
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"🌍 Web server started on port {port}")

# --- PROGRESS BAR ---
async def progress_bar(current, total, message, ud_type):
    now = time.time()
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
    
    if now - progress_bar.last_update > 5:
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

# --- DOWNLOAD LOGIC ---
def download_video(url):
    # Standard yt-dlp options with strong headers
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://hanime.tv/',
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **Bot is Alive!**\nSend a Hanime link. 🤖")

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(client, message: Message):
    url = message.text
    if "hanime.tv" not in url:
        await message.reply_text("❌ **Invalid Link!**")
        return

    status_msg = await message.reply_text("🔎 **Processing Link...** ⏳")

    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        progress_bar.start_time = time.time()
        await status_msg.edit_text("📥 **Downloading started...** 🚀")
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        await status_msg.edit_text("📤 **Upload started...** ⚡️")
        
        await message.reply_video(
            video=file_path,
            caption=f"✅ **Downloaded:** `{os.path.basename(file_path)}`",
            progress=progress_bar,
            progress_args=(status_msg, "Uploading...")
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:**\n`{str(e)}`")

# --- MAIN EXECUTION ---
async def main():
    # Pehle web server start karenge taaki Koyeb khush rahe
    await start_web_server()
    # Phir bot start karenge
    await app.start()
    print("🔥 Bot and Web Server are running!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
