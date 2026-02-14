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

# Yahan wo Session Token aayega jo aapne browser se nikala
# Koyeb ke Environment Variables mein HANIME_SESSION naam se add karna
HANIME_SESSION = os.environ.get("HANIME_SESSION", "")

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER ---
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

# --- PREMIUM DOWNLOADER ---
def download_video(url):
    slug = url.split('/hentai/')[-1].split('?')[0]
    api_url = f"https://hanime.tv/api/v8/video?id={slug}"
    
    # Headers mein Session Token add kar rahe hain
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Session-Token': HANIME_SESSION  # Ye line magic karegi
    }
    
    print(f"🔍 Fetching API (Logged-In Mode)...")
    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        data = r.json()
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")

    video_title = data['hentai_video']['name']
    video_title = "".join([c for c in video_title if c.isalnum() or c==' ']).strip()
    
    # Ab hume Premium Servers milenge
    valid_streams = []
    servers = data.get('videos_manifest', {}).get('servers', [])
    
    print(f"✅ Found {len(servers)} servers from API.")

    for server in servers:
        for stream in server.get('streams', []):
            link = stream['url']
            # Ab hume filter karne ki zarurat nahi, kyunki premium links usually ache hote hain
            if link and link not in valid_streams:
                valid_streams.append(link)

    if not valid_streams:
        raise Exception("Koi bhi video link nahi mila (Check Session Token).")

    output_file = f'downloads/{video_title}.mp4'
    
    for i, stream_url in enumerate(valid_streams):
        print(f"🚀 Trying Server {i+1}...")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_file,
            'quiet': True,
            'no_warnings': True,
            'http_headers': headers,
            'socket_timeout': 15,
            'ignoreerrors': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([stream_url])
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"✅ Success on Server {i+1}")
                return output_file
        except Exception as e:
            print(f"❌ Server {i+1} Failed. Trying next...")
            continue 

    raise Exception("Sabhi Premium Servers bhi fail ho gaye.")

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Premium Bot Ready!")

@app.on_message(filters.text)
async def handle_link(client, message: Message):
    if "hanime.tv" not in message.text: return

    status_msg = await message.reply_text("🔐 **Authenticating & Fetching...**")

    try:
        if not os.path.exists("downloads"): os.makedirs("downloads")
        progress_bar.start_time = time.time()
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, message.text)

        await status_msg.edit_text("📤 **Uploading Premium Video...**")
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
