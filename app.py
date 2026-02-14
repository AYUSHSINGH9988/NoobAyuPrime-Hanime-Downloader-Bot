import os
import time
import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8354139629:AAFXeLAl1kui4rdlMtKJkONHYlFttBDfh6w")

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER (Koyeb Alive Fix) ---
async def web_handler(request):
    return web.Response(text="Bot is Alive and Running!")

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

# --- SMART DOWNLOADER (Server Loop) ---
def download_video(url):
    try:
        slug = url.split('/hentai/')[-1].split('?')[0]
    except:
        raise Exception("Invalid URL. Make sure it contains '/hentai/'.")

    print(f"Fetching API for: {slug}")
    api_url = f"https://hanime.tv/api/v8/video?id={slug}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        data = r.json()
    except:
        raise Exception("Could not connect to Hanime API.")

    video_title = data['hentai_video']['name']
    video_title = "".join([c for c in video_title if c.isalnum() or c==' ']).strip()
    
    # --- MAGIC: Collect ALL Servers ---
    potential_streams = []
    servers = data.get('videos_manifest', {}).get('servers', [])
    
    for server in servers:
        for stream in server.get('streams', []):
            if stream['url'] and stream['url'] not in potential_streams:
                potential_streams.append(stream['url'])

    if not potential_streams:
        raise Exception("No video streams found in API.")

    # --- Loop through servers until one works ---
    output_file = f'downloads/{video_title}.mp4'
    last_error = ""

    for i, stream_url in enumerate(potential_streams):
        print(f"Trying Server {i+1}...")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_file,
            'quiet': True,
            'no_warnings': True,
            'http_headers': headers,
            # DNS fix options
            'socket_timeout': 10,
            'retries': 3,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([stream_url])
            
            # Agar file ban gayi, toh loop break karo
            if os.path.exists(output_file):
                print(f"Success on Server {i+1}")
                return output_file
        except Exception as e:
            print(f"Server {i+1} failed: {e}")
            last_error = str(e)
            continue # Try next server

    raise Exception(f"All servers failed. Last error: {last_error}")

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Bot Ready! Send link.")

@app.on_message(filters.text)
async def handle_link(client, message: Message):
    if "hanime.tv" not in message.text: return

    status_msg = await message.reply_text("🔄 **Finding working server...**")

    try:
        if not os.path.exists("downloads"): os.makedirs("downloads")
        progress_bar.start_time = time.time()
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, message.text)

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
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    app.run()
