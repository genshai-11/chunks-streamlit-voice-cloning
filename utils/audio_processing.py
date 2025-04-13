from utils.cloudinary_utils import upload_audio_to_cloudinary
from pydub import AudioSegment
import os
import shutil

# --- Set FFmpeg and ffprobe paths ---
fallback_ffmpeg_paths = ["/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]
fallback_ffprobe_paths = ["/usr/local/bin/ffprobe", "/usr/bin/ffprobe"]

ffmpeg_path = shutil.which("ffmpeg") or next((p for p in fallback_ffmpeg_paths if os.path.exists(p)), None)
ffprobe_path = shutil.which("ffprobe") or next((p for p in fallback_ffprobe_paths if os.path.exists(p)), None)

# Append to PATH for other libraries that may need it
if ffmpeg_path:
    os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)


# Debug PATH and tool availability
print(f"DEBUG: Current PATH: {os.environ.get('PATH')}")
print(f"DEBUG: ffmpeg path: {ffmpeg_path}, exists: {os.path.exists(ffmpeg_path)}")
print(f"DEBUG: ffprobe path: {ffprobe_path}, exists: {os.path.exists(ffprobe_path)}")

# Configure pydub with FFmpeg paths
if ffmpeg_path and os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
    print(f"✅ ffmpeg set to: {ffmpeg_path}")
else:
    raise Exception("ffmpeg not found or invalid path. Please ensure ffmpeg is installed.")

if ffprobe_path and os.path.exists(ffprobe_path):
    AudioSegment.ffprobe = ffprobe_path
    os.environ["FFPROBE_PATH"] = ffprobe_path
    print(f"✅ ffprobe set to: {ffprobe_path}")
else:
    print("⚠️ ffprobe not found. Proceeding without it, but some features may fail.")

# 🎧 Combine generated voice with background music
def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    """
    Combine a voice audio file with background music, applying fades and volume adjustments.
    
    Args:
        voice_path (str): Path to the voice audio file.
        music_path (str): Path to the background music file.
        output_path (str): Path where the merged audio will be saved.
        fade_in_ms (int): Fade-in duration in milliseconds.
        fade_out_ms (int): Fade-out duration in milliseconds.
        volume_reduction_db (int): Decibels to reduce music volume.
    
    Returns:
        str: Path to the merged audio file, or None if failed.
    """
    try:
        # Verify input files exist
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice file not found: {voice_path}")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Music file not found: {music_path}")
        print(f"DEBUG: Voice file: {voice_path}, size: {os.path.getsize(voice_path)} bytes")
        print(f"DEBUG: Music file: {music_path}, size: {os.path.getsize(music_path)} bytes")

        # Load audio files
        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)
        print(f"DEBUG: Voice duration: {len(voice)} ms, frame_rate: {voice.frame_rate}, channels: {voice.channels}")
        print(f"DEBUG: Music duration: {len(music)} ms, frame_rate: {music.frame_rate}, channels: {music.channels}")

        # Align music with voice properties
        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]  # Trim music to voice duration
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db
        print(f"DEBUG: Music adjusted - duration: {len(music)} ms, volume reduced by {volume_reduction_db} dB")

        # Combine audio
        combined = voice.overlay(music)
        print(f"DEBUG: Combined audio duration: {len(combined)} ms")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        print(f"DEBUG: Output directory created: {output_dir}")

        # Export the combined audio
        combined.export(output_path, format="mp3")
        print(f"DEBUG: Export completed to: {output_path}, size: {os.path.getsize(output_path)} bytes")

        # Verify output and upload to Cloudinary
        if os.path.exists(output_path):
            public_id = os.path.splitext(os.path.basename(output_path))[0]
            cloud_url = upload_audio_to_cloudinary(output_path, public_id=public_id, folder="Merge_Audio")
            if cloud_url:
                print(f"✅ Uploaded merged audio: {cloud_url}")
            else:
                print("⚠️ Cloudinary upload failed.")
        else:
            raise FileNotFoundError(f"Export succeeded but file not found: {output_path}")

        return output_path

    except Exception as e:
        print(f"❌ Error combining audio: {e}")
        return None
