from yt_dlp import YoutubeDL
import os
import shutil

def download_youtube_audio(url, output_dir):
    try:
        # 🔧 Get ffmpeg and ffprobe paths
        ffmpeg_dir = shutil.which("ffmpeg")
        ffprobe_dir = shutil.which("ffprobe")

        if not ffmpeg_dir or not ffprobe_dir:
            print("❌ ffmpeg or ffprobe not found. Please install or set PATH manually.")
            return None

        # Extract directory from full binary path
        ffmpeg_location = os.path.dirname(ffmpeg_dir)

        # Optional: set environment variables (helps other libs like imageio/moviepy)
        os.environ["PATH"] += os.pathsep + ffmpeg_location
        os.environ["FFMPEG_BINARY"] = ffmpeg_dir
        os.environ["FFPROBE_BINARY"] = ffprobe_dir

        print(f"🔧 Using ffmpeg at: {ffmpeg_dir}")
        print(f"🔧 Using ffprobe at: {ffprobe_dir}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_location,  # 👈 required for yt_dlp to find ffmpeg
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
