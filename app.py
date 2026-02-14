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

# --- WEB SERVER (Koyeb Fix) ---
async def web_handler(request):
    return web.Response(text="Bot is Alive!")

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

# --- IMPROVED DOWNLOADER ---
def download_video(url):
    slug = url.split('/hentai/')[-1].split('?')[0]
    api_url = f"https://hanime.tv/api/v8/video?id={slug}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    r = requests.get(api_url, headers=headers, timeout=10)
    data = r.json()

    video_title = data['hentai_video']['name']
    video_title = "".join([c for c in video_title if c.isalnum() or c==' ']).strip()
    
    valid_streams = []
    servers = data.get('videos_manifest', {}).get('servers', [])
    
    for server in servers:
        for stream in server.get('streams', []):
            if stream['url'] and stream['url'] not in valid_streams:
                valid_streams.append(stream['url'])

    output_file = f'downloads/{video_title}.mp4'
    
    # Servers ko try karne ka loop
    for i, stream_url in enumerate(valid_streams):
        print(f"🔄 Trying Mirror {i+1}...")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_file,
            'quiet': True,
            'no_warnings': True,
            'http_headers': headers,
            # DNS/Network Fixes
            'socket_timeout': 10,
            'retries': 2,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'ignoreerrors': True, # Taaki error aane par bot crash na ho
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Is function se hum check karte hain ki kya download start hua
                result = ydl.download([stream_url])
                
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                return output_file
        except Exception as e:
            print(f"❌ Mirror {i+1} failed. Moving to next...")
            continue 

    raise Exception("All video mirrors failed to resolve on Koyeb servers.")

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Bot Ready! Send link.")

@app.on_message(filters.text)
async def handle_link(client, message: Message):
    if "hanime.tv" not in message.text: return

    status_msg = await message.reply_text("🔄 **Checking all available mirrors...**")

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
 