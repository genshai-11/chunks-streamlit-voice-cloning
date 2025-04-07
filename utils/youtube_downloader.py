from yt_dlp import YoutubeDL
import os

def download_youtube_audio(url, output_dir):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "yt_audio")

        # ✅ Try to locate matching .mp3 file if the exact filename doesn't match
        mp3_files = [f for f in os.listdir(output_dir)
                     if f.endswith(".mp3") and title[:10] in f]

        if mp3_files:
            mp3_path = os.path.join(output_dir, mp3_files[0])
            print(f"✅ MP3 found: {mp3_path}")
            return mp3_path
        else:
            print("⚠️ MP3 file not found after download.")
            return None

    except Exception as e:
        print(f"❌ Failed to download audio: {e}")
        return None
