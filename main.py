import streamlit as st
from utils.helpers import generate_user_id, save_user_data, load_existing_users
from utils.speechify_api import get_voice_id, generate_audio_from_text
from utils.audio_processing import combine_voice_and_music
from utils.youtube_downloader import download_youtube_audio
from utils.helpers import load_text_inputs, save_text_template
import os, av, pydub
import queue
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase

# --- Initialization ---
st.set_page_config(page_title="Voice Cloning App", layout="wide")

data_folders = ["data/User_Records", "data/Generated_Audio", "data/Merge_Audio", "data/Background_Music"]
for folder in data_folders:
    os.makedirs(folder, exist_ok=True)

# --- Sidebar ---
with st.sidebar:
    st.image("assets/logo.png", width=120)
    st.title("Voice Cloning")
    selected = st.radio("Select Section", ["📤 Upload Voice", "🗣️ Generate Audio", "🎵 Merge with Music", "🗂️ Manage Files"], index=0)

st.title("🗣️ Voice Cloning with Background Music")

# Audio recorder setup
audio_queue = queue.Queue()
class AudioRecorder(AudioProcessorBase):
    def recv(self, frame):
        audio = frame.to_ndarray()
        audio_queue.put(audio)
        return frame

# --- Upload Voice ---
if selected.startswith("📤 Upload Voice"):
    st.header("🎤 Register New User's Voice")
    user_name = st.text_input("Full Name")
    email = st.text_input("Email (optional)")
    uploaded_audio = st.file_uploader("Upload your voice (MP3)", type=["mp3"], key="block1_audio")

    st.subheader("🎙️ Record Your Voice")
    ctx = webrtc_streamer(
        key="send-audio",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AudioRecorder,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )

    if st.button("Save Recording") and user_name:
        base = user_name.lower().replace(" ", "_") or "user"
        index = 1
        while True:
            user_id = f"{base}_{index:03}"
            file_path = f"data/User_Records/{user_id}.mp3"
            if not os.path.exists(file_path):
                break
            index += 1

        frames = []
        while not audio_queue.empty():
            frames.append(audio_queue.get())

        if frames:
            import numpy as np
            from scipy.io.wavfile import write

            wav_path = file_path.replace(".mp3", ".wav")
            combined = np.concatenate(frames, axis=0).astype(np.int16)
            write(wav_path, 48000, combined)

            sound = pydub.AudioSegment.from_wav(wav_path)
            sound.export(file_path, format="mp3")
            os.remove(wav_path)

            voice_id = get_voice_id(user_id, file_path)
            if voice_id:
                save_user_data(user_id, voice_id, user_name, email)
                st.success(f"✅ Recorded and registered! User ID: {user_id}, Voice ID: {voice_id}")
            else:
                st.error("❌ Failed to get voice ID.")
        else:
            st.warning("No audio recorded.")

    if st.button("Register Uploaded Voice") and uploaded_audio and user_name:
        base = user_name.lower().replace(" ", "_") or "user"
        index = 1
        while True:
            user_id = f"{base}_{index:03}"
            audio_path = f"data/User_Records/{user_id}.mp3"
            if not os.path.exists(audio_path):
                break
            index += 1

        with open(audio_path, "wb") as f:
            f.write(uploaded_audio.read())

        voice_id = get_voice_id(user_id, audio_path)
        if voice_id:
            save_user_data(user_id, voice_id, user_name, email)
            st.success(f"✅ Registered uploaded voice! User ID: {user_id}, Voice ID: {voice_id}")
        else:
            st.error("❌ Failed to get voice ID from Speechify.")

# --- Block 2: Generate Audio ---
elif selected.startswith("🗣️ Generate Audio"):
    st.header("🗣️ Generate Audio from Text")
    users = load_existing_users()
    selected_user = st.selectbox("Select User", list(users.keys()), key="block2_user")
    emotion = st.selectbox("Emotion", [None, "angry", "cheerful", "sad", "calm", "excited", "hopeful", "shouting", "terrified", "unfriendly", "whispering"])
    rate = st.slider("Speech Rate (Range -50 to +50)", -50, 50, 0)
    custom_text = st.text_area("Enter Text to Convert (optional)")

    uploaded_excel = st.file_uploader("Upload Excel file with text (optional)", type=["xlsx"], key="block2_excel")
    st.download_button("📥 Download Template", save_text_template(), file_name="Text_Template.xlsx")

    if st.button("Generate Audio"):
        texts = load_text_inputs(uploaded_excel, custom_text)
        for file_name, text in texts.items():
            rate_percent = int(rate)
            output_path = generate_audio_from_text(text, users[selected_user], selected_user, file_name, emotion, rate_percent)
            if output_path:
                st.audio(output_path)

# --- Block 3: Merge with Music ---
elif selected.startswith("🎵 Merge with Music"):
    st.header("🎶 Combine Voice Audio with Background Music")
    user_folder = st.selectbox("Select User Folder", os.listdir("data/Generated_Audio"), key="block3_user_folder")
    selected_audio = st.selectbox("Select Generated Audio", os.listdir(f"data/Generated_Audio/{user_folder}"), key="block3_audio")

    st.subheader("Select Background Music")
    music_option = st.radio("Music Source", ["Upload MP3", "YouTube Link"])
    music_path = ""

    if music_option == "Upload MP3":
        music_file = st.file_uploader("Upload Background Music", type=["mp3"], key="block3_upload_music")
        if music_file:
            music_path = f"data/Background_Music/{music_file.name}"
            with open(music_path, "wb") as f:
                f.write(music_file.read())
    else:
        youtube_url = st.text_input("Enter YouTube URL")
        if st.button("Download Music") and youtube_url:
            music_path = download_youtube_audio(youtube_url, "data/Background_Music")
            st.success(f"Downloaded and saved: {music_path}")

    fade_in = st.slider("Fade In (ms)", 0, 5000, 1000)
    fade_out = st.slider("Fade Out (ms)", 0, 5000, 1000)
    volume = st.slider("Volume Reduction (dB)", 0, 20, 5)

    if st.button("Merge Audio") and music_path:
        try:
            st.write("🔄 Merging audio... Please wait.")
            import time
            start_time = time.time()

            voice_path = f"data/Generated_Audio/{user_folder}/{selected_audio}"
            output_file = f"data/Merge_Audio/{user_folder}_{selected_audio.replace('.mp3', '_merged.mp3')}"
            combine_voice_and_music(voice_path, music_path, output_file, fade_in, fade_out, volume)

            end_time = time.time()
            st.success(f"🎉 Merged file saved: {output_file}")
            st.audio(output_file)
            st.write(f"✅ Merging completed in {end_time - start_time:.2f} seconds.")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

# --- Block 4: Manage Files ---
elif selected.startswith("🗂️ Manage Files"):
    st.header("🗂️ Manage Files")
    folders = {
        "User Records": "data/User_Records",
        "Generated Audio": "data/Generated_Audio",
        "Merged Audio": "data/Merge_Audio",
        "Background Music": "data/Background_Music"
    }
    tabs = st.tabs(list(folders.keys()))

    for tab, label in zip(tabs, folders.keys()):
        with tab:
            st.subheader(f"📁 {label}")
            folder_path = folders[label]
            if os.path.exists(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        st.write(f"📄 {file}")
                        if file.endswith(".mp3"):
                            st.audio(file_path)
                        with open(file_path, "rb") as f:
                            # Use the full file path as part of the key to ensure uniqueness
                            unique_key = file_path.replace("\\", "_").replace("/", "_")
                            st.download_button(
                                f"⬇️ Download {file}",
                                f,
                                file_name=file,
                                key=f"download_{unique_key}"
                            )
                        # Use the full file path as part of the key to ensure uniqueness
                        if st.button(f"🗑️ Delete {file}", key=f"delete_{unique_key}"):
                            os.remove(file_path)
                            st.warning(f"Deleted {file}")
                            st.experimental_rerun()
