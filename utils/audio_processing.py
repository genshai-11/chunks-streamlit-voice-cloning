from pydub import AudioSegment
import os
import shutil

# 🔧 Check if ffmpeg and ffprobe are available
ffmpeg_path = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
ffprobe_path = shutil.which("ffprobe") or "/usr/bin/ffprobe"

print(f"DEBUG: PATH: {os.environ.get('PATH')}")
print(f"DEBUG: ffmpeg path: {ffmpeg_path}, exists: {os.path.exists(ffmpeg_path)}")
print(f"DEBUG: ffprobe path: {ffprobe_path}, exists: {os.path.exists(ffprobe_path)}")

if ffmpeg_path and os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
    print(f"✅ ffmpeg set to: {ffmpeg_path}")
else:
    raise Exception("ffmpeg not found or invalid path.")

if ffprobe_path and os.path.exists(ffprobe_path):
    AudioSegment.ffprobe = ffprobe_path
    os.environ["FFPROBE_PATH"] = ffprobe_path
    print(f"✅ ffprobe set to: {ffprobe_path}")
else:
    print("⚠️ ffprobe not found, attempting to proceed without it.")

# 🎧 Combine generated voice with background music
def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    try:
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice file not found: {voice_path}")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Music file not found: {music_path}")
        print(f"DEBUG: Voice file: {voice_path}")
        print(f"DEBUG: Music file: {music_path}")

        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)

        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db

        combined = voice.overlay(music)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        print(f"DEBUG: Exporting to: {output_path}")
        combined.export(output_path, format="mp3")

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
