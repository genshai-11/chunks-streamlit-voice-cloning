from yt_dlp import YoutubeDL
import os
import shutil

def download_youtube_audio(url, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        ffmpeg_dir = shutil.which("ffmpeg")
        ffprobe_dir = shutil.which("ffprobe")
        print(f"DEBUG: ffmpeg path: {ffmpeg_dir}")
        print(f"DEBUG: ffprobe path: {ffprobe_dir}")
        if not ffmpeg_dir or not ffprobe_dir:
            raise Exception("ffmpeg or ffprobe not found. Please install or set PATH manually.")

        ffmpeg_location = os.path.dirname(ffmpeg_dir)
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
            'ffmpeg_location': ffmpeg_location,
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info)
            mp3_path = base_filename.rsplit('.', 1)[0] + '.mp3'

        if os.path.exists(mp3_path):
            print(f"✅ MP3 found: {mp3_path}")
            return mp3_path
        else:
            raise Exception("MP3 file not found after download.")

    except Exception as e:
        print(f"❌ Failed to download audio: {e}")
        raise Exception(f"Download failed: {str(e)}")
