import os
import time
import asyncio
import requests
from pyrogram import Client, filters, idle
from pyrogram.types import Message
import yt_dlp
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8354139629:AAFXeLAl1kui4rdlMtKJkONHYlFttBDfh6w")

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER (Koyeb Fix) ---
async def web_handler(request):
    return web.Response(text="Bot is Running!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", web_handler)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- PROGRESS BAR ---
async def progress_bar(current, total, message, ud_type):
    now = time.time()
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
    
    if now - progress_bar.last_update > 5:
        try:
            percentage = current * 100 / total
            speed = current / (now - progress_bar.start_time)
            await message.edit_text(
                f"⚡️ **{ud_type}**\n"
                f"📊 {percentage:.1f}% | 🚀 {speed/1024/1024:.2f} MB/s"
            )
        except:
            pass
        progress_bar.last_update = now

# --- NEW DOWNLOAD LOGIC (API BYPASS) ---
def download_video(url):
    # 1. URL se Slug nikalo (e.g. video-name-1)
    try:
        slug = url.split('/hentai/')[-1].split('?')[0]
    except IndexError:
        raise Exception("Invalid URL format. '/hentai/' not found.")

    # 2. Direct API Call (Website Bypass)
    api_url = f"https://hanime.tv/api/v8/video?id={slug}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Directive': 'api'
    }
    
    print(f"Fetching API for slug: {slug}")
    response = requests.get(api_url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"API Blocked or Video Not Found (Status: {response.status_code})")

    data = response.json()
    
    # 3. JSON se .m3u8 Link Nikalo
    try:
        # Hanime API structure often changes, checking common paths
        if 'videos_manifest' in data:
            servers = data['videos_manifest']['servers']
            # Loop through servers to find a valid stream
            stream_url = servers[0]['streams'][0]['url']
        else:
            raise Exception("Video stream not found in API response.")
            
        video_title = data['hentai_video']['name']
        # Clean title for filename
        video_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    except Exception as e:
        raise Exception(f"Failed to parse API JSON: {str(e)}")

    print(f"Stream Found: {stream_url}")

    # 4. Pass DIRECT STREAM LINK to yt-dlp (Not the website link)
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'downloads/{video_title}.mp4',
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([stream_url])
        return f"downloads/{video_title}.mp4"

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Bot is Ready! Send Link.")

@app.on_message(filters.text)
async def handle_link(client, message: Message):
    url = message.text
    if "hanime.tv" not in url:
        return

    status_msg = await message.reply_text("🕵️ **Hacking into Hanime API...**")

    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        progress_bar.start_time = time.time()
        
        loop = asyncio.get_event_loop()
        # Ab hum 'download_video' function call kar rahe hain jo API use karega
        file_path = await loop.run_in_executor(None, download_video, url)

        await status_msg.edit_text("📤 **Uploading...**")
        
        await message.reply_video(
            video=file_path,
            caption=f"🎥 `{os.path.basename(file_path)}`",
            progress=progress_bar,
            progress_args=(status_msg, "Uploading")
        )
        
        os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Failed:** {str(e)}\n\n_Koyeb IP might be banned._")

# --- RUNNER ---
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    app.run()
