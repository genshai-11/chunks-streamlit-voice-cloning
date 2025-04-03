# 🗣️ Voice Cloning App with Background Music 🎵

A Streamlit-powered web app that allows users to:
- 🎙️ Record or upload their voice
- 🔁 Clone it using the Speechify API
- 📄 Generate speech from text (Excel/manual)
- 🎧 Merge it with background music (uploaded or from YouTube)
- 🗂️ Manage all audio files in one place

---

## 🚀 Features

### 📤 Upload Voice
- Upload `.mp3` or record directly in-browser
- Auto-save recording, convert to `.mp3`
- Smart user ID generation (e.g., `john_001`)
- Registers and gets `voice_id` via Speechify API

### 🗣️ Generate Audio
- Select any user’s voice
- Enter or upload text (Excel)
- Adjust emotion and speech rate
- Generates `.mp3` files with custom voice

### 🎵 Merge with Music
- Upload music or enter a YouTube link
- Auto-trim, fade-in/out, volume control
- Merge generated voice with background music

### 🗂️ Manage Files
- Tab-based file browser
- Preview audio
- Download or delete `.mp3` files

---

## 📁 Project Structure

```
voice_cloning_app/
├── main.py
├── requirements.txt
├── utils/
│   ├── helpers.py
│   ├── speechify_api.py
│   ├── audio_processing.py
│   └── youtube_downloader.py
├── data/
│   ├── User_Records/
│   ├── Generated_Audio/
│   ├── Merged_Audio/
│   └── Background_Music/
└── assets/
    └── logo.png
```

---

## 🛠️ Installation

1. **Clone the repo**:
```bash
git clone https://github.com/myle1996kh/chunks-voice-cloning-with-bgmusic.git
cd chunks-voice-cloning-with-bgmusic
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **(Optional) Install FFmpeg**  
Pydub needs FFmpeg to convert `.wav` to `.mp3`.

---

## ▶️ Run the App

```bash
streamlit run main.py
```

---

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub  
2. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)  
3. Click **“New App”** and select your repo  
4. Set `main.py` as entry point  
5. Deploy!

---

## 💬 Credits

Built by [@myle1996kh](https://github.com/myle1996kh)  
Voice cloning via [Speechify API]  
Recording via `streamlit-webrtc`  
Music merging via `pydub`

---

## 🧠 Coming Soon

- Save and playback recordings before upload  
- User authentication  
- Export to Google Drive  
