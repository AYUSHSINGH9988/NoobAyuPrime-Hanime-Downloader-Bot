import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

# --- CONFIGURATION ---
# Replace these with your actual credentials from my.telegram.org
API_ID = "YOUR_API_ID" 
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "8354139629:AAFXeLAl1kui4rdlMtKJkONHYlFttBDfh6w"

app = Client("hanime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- PROGRESS BAR LOGIC ---
async def progress_bar(current, total, message, ud_type):
    now = time.time()
    # Update every 3 seconds to avoid Telegram flood limits
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
    
    if now - progress_bar.last_update > 3:
        percentage = current * 100 / total
        elapsed_time = now - progress_bar.start_time
        speed = current / elapsed_time if elapsed_time > 0 else 0
        
        progress_str = f"**{ud_type}**\n"
        progress_str += f"📊 **Progress:** {percentage:.2f}%\n"
        progress_str += f"🚀 **Speed:** {speed/1024:.2f} KB/s\n"
        progress_str += f"📁 **Done:** {current/(1024*1024):.2f} MB / {total/(1024*1024):.2f} MB"
        
        try:
            await message.edit_text(progress_str)
        except:
            pass
        progress_bar.last_update = now

# --- DOWNLOAD LOGIC ---
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

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    welcome_text = (
        "👋 **Hello there!**\n\n"
        "I am your **Hanime Downloader Bot**. 🤖\n"
        "Just send me a valid link, and I will download & upload it for you! 📥✨\n\n"
        "🚀 **Fast & Simple!** Give it a try."
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(client, message: Message):
    url = message.text
    if "hanime.tv" not in url:
        await message.reply_text("❌ **Invalid Link!** Please send a proper Hanime.tv URL.")
        return

    status_msg = await message.reply_text("🔎 **Checking link... Please wait.** ⏳")

    try:
        # Create downloads folder if not exists
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        progress_bar.start_time = time.time()
        await status_msg.edit_text("📥 **Downloading started...**\nFetching video from servers! 🚀")
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        # Upload phase
        await status_msg.edit_text("📤 **Download complete!**\nNow uploading to Telegram... ⚡")
        
        await message.reply_video(
            video=file_path,
            caption=f"✅ **Success!**\n🎥 **File:** `{os.path.basename(file_path)}`",
            progress=progress_bar,
            progress_args=(status_msg, "Uploading to Telegram... 📤")
        )
        
        # Cleanup storage
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **An Error Occurred:**\n`{str(e)}`")

print("🔥 Bot is live and running!")
app.run()

