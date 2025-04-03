import yt_dlp
import os

def download_youtube_audio(url, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            return os.path.join(output_dir, f"{result['title']}.mp3")
    except Exception as e:
        print(f"❌ Failed to download audio: {e}")
        return None
