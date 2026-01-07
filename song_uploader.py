import os
import yt_dlp
import sys

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "My_MP3_Downloads"
FFMPEG_PATH = os.getcwd()  # Make sure ffmpeg.exe is in the same folder

def progress_hook(d):
    """Shows download progress bar"""
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%')
            s = d.get('_speed_str', 'N/A')
            sys.stdout.write(f"\r⬇️  Downloading... {p} | Speed: {s} ")
            sys.stdout.flush()
        except: pass
    if d['status'] == 'finished':
        print("\n✅ Downloaded. Mastering Audio (Cleaning & Normalizing)...")

def download_track(youtube_url):
    """Downloads Video, Converts to 320kbps MP3, Normalizes Volume"""
    
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    out_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # Force 320kbps
            }
        ],
        # 🔥 AUDIO ENGINEERING MAGIC HERE 🔥
        'postprocessor_args': [
            '-ar', '44100',       # Fix Sample Rate to Studio Standard (44.1kHz)
            '-ac', '2',           # Force Stereo (2 Channels)
            '-b:a', '320k',       # Ensure Bitrate stays 320k during filtering
            '-af', 'volume=0.85', # Reduce Gain by 15% (Fixes "Phata Hua" Speaker Sound)
        ],
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
        'restrictfilenames': False, # Keep original spaces/emojis in title
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🔍 Processing: {youtube_url}")
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown Title')
            print(f"🎉 Success! Saved: {title}.mp3")
            return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

# --- MAIN LOOP ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" 🎵 AIRSPACE STUDIO DOWNLOADER (FINAL EDITION) 🎵")
    print(" Features: 320kbps | 44.1kHz | Anti-Clipping (Clean Audio)")
    print(f" 📂 Saving to: {DOWNLOAD_FOLDER}")
    print("="*60 + "\n")
    
    while True:
        link = input("🔗 Paste YouTube Link (or type 'q' to quit): ").strip()
        
        if link.lower() in ['q', 'exit', 'done']: 
            print("\n👋 Exiting... Enjoy your music!")
            break
        
        if link: 
            download_track(link)
            print("-" * 50)