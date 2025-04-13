import streamlit as st
from utils.helpers import generate_user_id, save_user_data, load_existing_users, load_text_inputs, save_text_template
from utils.youtube_downloader import download_youtube_audio
from utils.speechify_api import get_voice_id, generate_audio_from_text
from utils.cloudinary_utils import upload_audio_to_cloudinary
from utils.github_utils import upload_excel_to_github
from utils.audio_processing import combine_voice_and_music
from openpyxl import Workbook, load_workbook
from streamlit_option_menu import option_menu
import os
import pandas as pd
import uuid
import time
import shutil
import io
from PIL import Image


# Ensure FFmpeg is in PATH for Streamlit Cloud
os.environ["PATH"] += os.pathsep + "/usr/bin"

# --- Initialization ---
st.set_page_config(page_title="Voice Cloning App", layout="wide")
folders = ["data/User_Records", "data/Generated_Audio", "data/Merge_Audio", "data/Background_Music"]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# --- Sidebar ---
with st.sidebar:
    st.image("assets/logo.png", width=120)
    st.title("Voice Cloning")

    section_options = [
        "📤 Upload Voice",
        "🗣️ Generate Audio",
        "🎵 Merge with Music",
        "🗂️ Manage Files",
        "📄 User Data"
    ]

    selected = st.selectbox("Choose Section", section_options)


st.title("🗣️ Voice Cloning with Background Music")

# --- Block 1: Upload Voice ---
if selected.startswith("📤 Upload Voice"):
    st.header("🎤 Register New User's Voice")
    user_name = st.text_input("Full Name")
    email = st.text_input("Email (optional)")
    uploaded_audio = st.file_uploader("Upload MP3 voice file", type=["mp3"])

    if st.button("Register Uploaded Voice") and uploaded_audio:
        user_id = generate_user_id(user_name)
        audio_path = f"data/User_Records/{user_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(uploaded_audio.read())

        cloud_url = upload_audio_to_cloudinary(audio_path, folder="User_Records", public_id=user_id)
        voice_id = get_voice_id(user_id, audio_path)

        if voice_id:
            save_user_data(user_id, voice_id, user_name, email)
            st.success(f"✅ Voice registered for User ID: {user_id}")
            if cloud_url:
                st.markdown(f"[Cloudinary Link]({cloud_url})")
        else:
            st.error("❌ Failed to get voice ID from Speechify.")

# --- Block 2: Generate Audio ---
elif selected.startswith("🗣️ Generate Audio"):
    st.header("🗣️ Generate Audio from Text")
    users = load_existing_users()
    selected_user = st.selectbox("Select User", list(users.keys()))
    emotion = st.selectbox("Emotion", [None, "angry", "cheerful", "sad", "calm"])
    rate = st.slider("Speech Rate (-50 to +50)", -50, 50, 0)
    custom_text = st.text_area("Text to convert (optional)")
    uploaded_excel = st.file_uploader("Excel with texts (optional)", type=["xlsx"])

    st.download_button("Download Excel Template", save_text_template(), file_name="Text_Template.xlsx")

    if st.button("Generate Audio"):
        texts = load_text_inputs(uploaded_excel, custom_text)
        for _, text in texts.items():
            file_name = f"{uuid.uuid4().hex[:8]}"
            output_path = generate_audio_from_text(text, users[selected_user], selected_user, file_name, emotion, rate)
            
            if output_path:
                cloud_url = upload_audio_to_cloudinary(output_path, folder="Generated_Audio", public_id=file_name)
                st.audio(output_path)
                if cloud_url:
                    st.markdown(f"[Cloudinary Link]({cloud_url})")
            else:
                st.error("❌ Failed to generate audio.")

# --- Block 3: Merge with Music ---
elif selected.startswith("🎵 Merge with Music"):
    st.header("🎶 Merge Voice Audio with Background Music")
    
    generated_audio_path = "data/Generated_Audio"
    available_folders = [f for f in os.listdir(generated_audio_path) if os.path.isdir(os.path.join(generated_audio_path, f))]
    
    if not available_folders:
        st.warning("⚠️ No generated audio folders found. Please generate some audio first.")
    else:
        user_folder = st.selectbox("Select User", available_folders)
        audio_files = [f for f in os.listdir(f"data/Generated_Audio/{user_folder}") if f.endswith(".mp3")]
        
        if not audio_files:
            st.warning("⚠️ No audio files found in this folder.")
        else:
            selected_audio = st.selectbox("Select Audio", audio_files)
            
            music_option = st.radio("Music Source", ["Upload MP3", "YouTube Link", "Select from Library"])
            music_path = ""

            if music_option == "Upload MP3":
                music_file = st.file_uploader("Upload MP3", type=["mp3"])
                if music_file:
                    music_path = f"data/Background_Music/{music_file.name}"
                    with open(music_path, "wb") as f:
                        f.write(music_file.read())

            elif music_option == "YouTube Link":
                youtube_url = st.text_input("YouTube URL")
                if st.button("Download from YouTube") and youtube_url:
                    with st.spinner("Downloading from YouTube..."):
                        try:
                            music_path = download_youtube_audio(youtube_url, "data/Background_Music")
                        except Exception as e:
                            st.error(f"❌ Download failed: {str(e)}")
                            music_path = None
                    if music_path and os.path.exists(music_path):
                        st.success(f"✅ Audio downloaded: {os.path.basename(music_path)}")
                        music_cloud_url = upload_audio_to_cloudinary(music_path, folder="Background_Music")
                        if music_cloud_url:
                            st.markdown(f"[Cloudinary Link]({music_cloud_url})")
                        if st.button("Refresh Library"):
                            st.rerun()

            elif music_option == "Select from Library":
                tracks = [f for f in os.listdir("data/Background_Music") if f.endswith(".mp3")]
                if tracks:
                    selected_track = st.selectbox("Choose track", tracks)
                    music_path = os.path.join("data/Background_Music", selected_track)
                else:
                    st.warning("⚠️ No background music tracks available.")

            fade_in = st.slider("Fade In (ms)", 0, 5000, 1000)
            fade_out = st.slider("Fade Out (ms)", 0, 5000, 1000)
            volume = st.slider("Volume Reduction (dB)", 0, 20, 5)

            if st.button("Merge") and music_path:
                voice_path = f"data/Generated_Audio/{user_folder}/{selected_audio}"
                output_file = f"data/Merge_Audio/{user_folder}/{selected_audio.replace('.mp3', '_merged.mp3')}"
                with st.spinner("Merging audio..."):
                    result = combine_voice_and_music(voice_path, music_path, output_file, fade_in, fade_out, volume)
                if result and os.path.exists(result):
                    merged_cloud_url = upload_audio_to_cloudinary(output_file, folder="Merge_Audio")
                    st.success("🎉 Merged successfully!")
                    st.audio(output_file)
                    if merged_cloud_url:
                        st.markdown(f"[Cloudinary Link]({merged_cloud_url})")
                else:
                    st.error("❌ Failed to merge audio. Check logs for details.")

# --- Block 4: Manage Files ---
elif selected.startswith("🗂️ Manage Files"):
    st.header("🗂️ Manage Files")
    folders = ["User_Records", "Generated_Audio", "Merge_Audio", "Background_Music"]
    tab = st.tabs(folders)

    import librosa
    import matplotlib.pyplot as plt
    import numpy as np

    @st.cache_data
    def plot_waveform(audio_path):
        try:
            y, sr = librosa.load(audio_path, sr=None)
            plt.figure(figsize=(4, 1), dpi=100)
            plt.plot(y, color="#1f77b4")
            plt.axis("off")
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
            plt.close()
            buf.seek(0)
            return Image.open(buf)
        except Exception as e:
            st.error(f"Failed to generate waveform for {audio_path}: {str(e)}")
            return None

    for folder, t in zip(folders, tab):
        with t:
            base_path = f"data/{folder}"
            audio_extensions = (".mp3", ".wav", ".ogg")
            audio_files = []

            if folder in ["Generated_Audio", "Merge_Audio"]:
                for user_folder in os.listdir(base_path):
                    user_path = os.path.join(base_path, user_folder)
                    if os.path.isdir(user_path):
                        for file in os.listdir(user_path):
                            file_path = os.path.join(user_path, file)
                            if os.path.isfile(file_path) and file.lower().endswith(audio_extensions):
                                audio_files.append((user_folder, file, file_path))
            else:
                for file in os.listdir(base_path):
                    file_path = os.path.join(base_path, file)
                    if os.path.isfile(file_path) and file.lower().endswith(audio_extensions):
                        audio_files.append((None, file, file_path))

            if not audio_files:
                st.write("No audio files found in this folder.")
                continue

            for user_folder, file, path in audio_files:
                path = path.replace("\\", "/")
                display_name = f"{user_folder}/{file}" if user_folder else file

                col1, col2, col3, col4 = st.columns([2, 3, 3, 1])

                with col1:
                    y, sr = librosa.load(path, sr=None)
                    duration = librosa.get_duration(y=y, sr=sr)
                    file_size = os.path.getsize(path) / 1024
                    st.write(f"🎵 {display_name} ({duration:.2f}s, {file_size:.2f} KB)")

                with col2:
                    waveform_image = plot_waveform(path)
                    if waveform_image:
                        st.image(waveform_image, use_container_width=True)

                with col3:
                    try:
                        st.audio(path)
                    except Exception as e:
                        st.error(f"❌ Failed to play {display_name}: {str(e)}")

                with col4:
                    with open(path, "rb") as f:
                        st.download_button(
                            label="⬇️",
                            data=f,
                            file_name=file,
                            key=f"download_{folder}_{user_folder}_{file}"
                        )
                    if st.button("🗑️", key=f"del_{folder}_{user_folder}_{file}"):
                        os.remove(path)
                        st.warning(f"Deleted {display_name}")
                        st.rerun()

                st.markdown("---")

# --- Block 5: User Data Management ---
elif selected.startswith("📄 User Data"):
    st.header("📄 User Data Management")
    path = "data/User_Data.xlsx"
    if os.path.exists(path):
        df = pd.read_excel(path)
        st.download_button("⬇️ Download User_Data.xlsx", open(path, "rb"), "User_Data.xlsx")
        
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Save Changes"):
            edited_df.to_excel(path, index=False)
            st.success("✅ Changes saved!")

        if st.button("☁️ Upload to GitHub"):
            token = st.text_input("GitHub Token", type="password")
            repo_name = st.text_input("Repo (username/repo)")
            if token and repo_name:
                upload_excel_to_github(token, repo_name, path)
                st.success("✅ Uploaded to GitHub")
            else:
                st.warning("⚠️ Enter token and repo name")
