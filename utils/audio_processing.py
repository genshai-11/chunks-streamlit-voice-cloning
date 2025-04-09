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
import subprocess

def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    try:
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice file not found: {voice_path}")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Music file not found: {music_path}")

        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)

        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db

        combined = voice.overlay(music)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            combined.export(output_path, format="mp3")
        except Exception as export_error:
            # Debug FFmpeg directly
            cmd = [AudioSegment.ffmpeg, "-i", voice_path, "-i", music_path, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"DEBUG: FFmpeg stderr: {result.stderr}")
            raise Exception(f"Export failed: {export_error}, FFmpeg output: {result.stderr}")

        if os.path.exists(output_path):
            public_id = os.path.splitext(os.path.basename(output_path))[0]
            cloud_url = upload_audio_to_cloudinary(output_path, public_id=public_id)
            if cloud_url:
                print(f"✅ Uploaded merged audio: {cloud_url}")
        else:
            raise FileNotFoundError(f"Export succeeded but file not found: {output_path}")

        return output_path
    except Exception as e:
        print(f"❌ Error combining audio: {e}")
        return None
