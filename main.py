import streamlit as st
from utils.helpers import generate_user_id, save_user_data, load_existing_users, load_text_inputs, save_text_template
from utils.speechify_api import get_voice_id, generate_audio_from_text
from utils.audio_processing import combine_voice_and_music
from utils.youtube_downloader import download_youtube_audio
from utils.cloudinary_utils import upload_audio_to_cloudinary
from utils.github_utils import upload_excel_to_github
import os, pandas as pd, uuid
import time

# --- Initialization ---
st.set_page_config(page_title="Voice Cloning App", layout="wide")

folders = ["data/User_Records", "data/Generated_Audio", "data/Merge_Audio", "data/Background_Music"]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# --- Sidebar ---
with st.sidebar:
    st.image("assets/logo.png", width=120)
    st.title("Voice Cloning")
    selected = st.radio(
        "Select Section",
        ["📤 Upload Voice", "🗣️ Generate Audio", "🎵 Merge with Music", "🗂️ Manage Files", "📄 User Data"],
        index=0
    )

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

# --- Block 3: Merge with Music ---
elif selected.startswith("🎵 Merge with Music"):
    st.header("🎶 Merge Voice Audio with Background Music")
    user_folder = st.selectbox("Select User", os.listdir("data/Generated_Audio"))
    selected_audio = st.selectbox("Select Audio", os.listdir(f"data/Generated_Audio/{user_folder}"))
    
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
            music_path = download_youtube_audio(youtube_url, "data/Background_Music")
            if music_path:
                music_cloud_url = upload_audio_to_cloudinary(music_path, folder="Background_Music")
                st.success(f"✅ Uploaded: [Link]({music_cloud_url})")
            else:
                st.error("❌ YouTube download failed.")

    elif music_option == "Select from Library":
        tracks = [f for f in os.listdir("data/Background_Music") if f.endswith(".mp3")]
        if tracks:
            selected_track = st.selectbox("Choose track", tracks)
            music_path = os.path.join("data/Background_Music", selected_track)

    fade_in = st.slider("Fade In (ms)", 0, 5000, 1000)
    fade_out = st.slider("Fade Out (ms)", 0, 5000, 1000)
    volume = st.slider("Volume Reduction (dB)", 0, 20, 5)

    if st.button("Merge") and music_path:
        voice_path = f"data/Generated_Audio/{user_folder}/{selected_audio}"
        output_file = f"data/Merge_Audio/{user_folder}_{selected_audio.replace('.mp3', '_merged.mp3')}"

        combine_voice_and_music(voice_path, music_path, output_file, fade_in, fade_out, volume)
        merged_cloud_url = upload_audio_to_cloudinary(output_file, folder="Merge_Audio")

        st.success("🎉 Merged successfully!")
        st.audio(output_file)
        if merged_cloud_url:
            st.markdown(f"[Cloudinary Link]({merged_cloud_url})")

# --- Block 4: Manage Files ---
elif selected.startswith("🗂️ Manage Files"):
    st.header("🗂️ Manage Files")
    folders = ["User_Records", "Generated_Audio", "Merge_Audio", "Background_Music"]
    tab = st.tabs(folders)

    for folder, t in zip(folders, tab):
        with t:
            files = os.listdir(f"data/{folder}")
            for file in files:
                path = os.path.join(f"data/{folder}", file)
                st.write(f"🎵 {file}")
                st.audio(path)
                with open(path, "rb") as f:
                    st.download_button("⬇️", f, file_name=file, key=f"{folder}_{file}")
                if st.button("🗑️", key=f"del_{folder}_{file}"):
                    os.remove(path)
                    st.warning(f"Deleted {file}")
                    st.experimental_rerun()

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
