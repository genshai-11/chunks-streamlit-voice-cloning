from utils.cloudinary_utils import upload_audio_to_cloudinary
from pydub import AudioSegment
import os
import shutil

# 🔧 Check if ffmpeg and ffprobe are available
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
    print(f"✅ ffmpeg found at: {ffmpeg_path}")
else:
    print("❌ ffmpeg not found. Please install it or add it to PATH.")
    print("🛠️ On Ubuntu: sudo apt install ffmpeg")
    print("🛠️ On Mac: brew install ffmpeg")
    print("🛠️ On Windows: https://ffmpeg.org/download.html")

if ffprobe_path:
    os.environ["FFPROBE_PATH"] = ffprobe_path
    print(f"✅ ffprobe found at: {ffprobe_path}")
else:
    print("❌ ffprobe not found. Some tools may not work properly.")

# 🎧 Combine generated voice with background music
def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    try:
        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)

        # Align music with voice duration and format
        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db

        # Overlay voice on top of background music
        combined = voice.overlay(music)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        combined.export(output_path, format="mp3")

        # ✅ Upload to Cloudinary
        if os.path.exists(output_path):
            public_id = os.path.splitext(os.path.basename(output_path))[0]
            cloud_url = upload_audio_to_cloudinary(output_path, public_id=public_id)
            if cloud_url:
                print(f"✅ Uploaded merged audio: {cloud_url}")
        else:
            print(f"❌ Export failed, file not found: {output_path}")

        return output_path
    except Exception as e:
        print(f"❌ Error combining audio: {e}")
        return None
