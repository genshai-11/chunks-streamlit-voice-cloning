from utils.cloudinary_utils import upload_audio_to_cloudinary
from pydub import AudioSegment
import os
from pydub import AudioSegment
import shutil

# Check if ffmpeg is available, or set path manually
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
else:
    print("⚠️ Warning: ffmpeg not found. Audio processing may fail. Please install ffmpeg and add it to PATH.")
#--
def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    try:
        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)

        # Căn chỉnh nhạc nền với voice
        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db

        # Kết hợp 2 âm thanh
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
