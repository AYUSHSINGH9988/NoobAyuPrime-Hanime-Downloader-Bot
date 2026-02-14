import os
import time
import asyncio
import requests
import json
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- SESSION TOKEN CLEANER (Automatic Fix) ---
# Agar token mein '(-(0)-)' jaisa kuch hua, toh ye use hata dega
raw_session = os.environ.get("HANIME_SESSION", "")
HANIME_SESSION = raw_session.split('(')[0].strip()

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER (To Keep Bot Alive on Koyeb) ---
async def web_handler(request):
    return web.Response(text="Bot is Alive and Running!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", web_handler)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print("🌍 Web Server Started.")

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

# --- ULTIMATE DOWNLOADER LOGIC ---
def download_video(url):
    # 1. URL se ID (Slug) nikalo
    try:
        slug = url.split('/hentai/')[-1].split('?')[0]
    except:
        raise Exception("Invalid URL. '/hentai/' nahi mila.")

    print(f"🔍 Analyzing: {slug}")
    
    # 2. API Headers (Fake Android Device)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        'Cookie': f'htv3session={HANIME_SESSION}',
        'X-Directive': 'api',
        'Accept': 'application/json',
    }
    
    # 3. API Call
    api_url = f"https://hanime.tv/api/v8/video?id={slug}"
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code != 200:
            raise Exception(f"API Error Code: {r.status_code}")
        data = r.json()
    except Exception as e:
        raise Exception(f"API Connection Failed: {str(e)}")

    # 4. Name Cleaning
    video_title = data['hentai_video']['name']
    safe_title = "".join([c for c in video_title if c.isalnum() or c==' ']).strip()
    output_file = f'downloads/{safe_title}.mp4'

    # 5. Extract ALL Possible Streams
    stream_urls = []
    
    # Priority 1: Manifest Servers (Highest Quality)
    manifest = data.get('videos_manifest', {})
    for server in manifest.get('servers', []):
        for stream in server.get('streams', []):
            if stream.get('url'):
                stream_urls.append(stream['url'])

    # Priority 2: Direct Video Object (Fallback)
    if not stream_urls:
        for vid in data.get('videos', []):
            if vid.get('url'):
                stream_urls.append(vid['url'])
                
    if not stream_urls:
        raise Exception("Login ke bawajood koi video link nahi mila. Token Expired?")

    print(f"🎯 Found {len(stream_urls)} servers. Starting attack...")

    # 6. Try Each Stream Until One Works
    for i, link in enumerate(stream_urls):
        print(f"🔄 Attempt {i+1}/{len(stream_urls)}...")
        
        # Dead Server Skip
        if "streamable.cloud" in link:
            print("⚠️ Skipping known bad server (DNS Issue).")
            # Hum isko sirf tab try karenge agar baaki sab fail ho jayein
            # (Lekin abhi ke liye skip karte hain time bachane ke liye)
            continue

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_file,
            'quiet': True,
            'http_headers': headers,
            'nocheckcertificate': True, # SSL Errors Ignore
            'ignoreerrors': True,
            'socket_timeout': 10,
            'retries': 5,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            
            # Check if download actually happened
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
                print(f"✅ Success on Server {i+1}!")
                return output_file
        except Exception as e:
            print(f"❌ Server {i+1} Failed: {e}")
            continue

    # 7. Last Resort (Try 'Bad' Servers if clean ones failed)
    print("⚠️ Clean servers failed. Trying risky servers...")
    for link in stream_urls:
        if "streamable.cloud" in link:
             # Try generic download
             try:
                ydl_opts = {'outtmpl': output_file, 'nocheckcertificate': True, 'ignoreerrors': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([link])
                if os.path.exists(output_file): return output_file
             except: pass

    raise Exception("All mirrors failed. Koyeb IP is fully blocked.")

# --- HANDLERS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **Final Hanime Bot**\nLogged in & Ready to Bypass! 🛡️")

@app.on_message(filters.text)
async def handle_link(client, message: Message):
    url = message.text
    if "hanime.tv" not in url:
        return

    status = await message.reply_text("🕵️ **Hacking Mainframe... (Logging in)**")

    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        progress_bar.start_time = time.time()
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        await status.edit_text("📤 **Got it! Uploading...**")
        
        await message.reply_video(
            video=file_path,
            caption=f"🎥 **{os.path.basename(file_path)}**\n✅ *Premium Download*",
            progress=progress_bar,
            progress_args=(status, "Uploading")
        )
        
        os.remove(file_path)
        await status.delete()

    except Exception as e:
        await status.edit_text(f"💀 **Fatal Error:**\n`{str(e)}`")

# --- MAIN RUNNER ---
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    app.run()
