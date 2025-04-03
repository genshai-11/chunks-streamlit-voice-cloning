from pydub import AudioSegment
import os

def combine_voice_and_music(voice_path, music_path, output_path, fade_in_ms=1000, fade_out_ms=1000, volume_reduction_db=5):
    try:
        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)
        music = music.set_frame_rate(voice.frame_rate).set_channels(voice.channels)
        music = music[:len(voice)]
        music = music.fade_in(fade_in_ms).fade_out(fade_out_ms) - volume_reduction_db
        combined = voice.overlay(music)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        combined.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        print(f"❌ Error combining audio: {e}")
        return None
