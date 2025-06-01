import requests
import base64
import os
import xml.sax.saxutils as xml_escape

API_KEY = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="  # Replace with your key if needed

def get_voice_id(name, audio_file_path):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    with open(audio_file_path, "rb") as f:
        files = {"sample": f}
        data = {"name": name, "consent": '{"fullName": "User", "email": "user@example.com"}'}
        response = requests.post("https://api.sws.speechify.com/v1/voices", headers=headers, files=files, data=data)
    if response.status_code == 200:
        return response.json().get("id")
    return None

def generate_audio_from_text(text, voice_id, user_id, file_name, emotion=None, rate="medium"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Escape the input text to prevent XML issues
    safe_text = xml_escape.escape(text)

    # Construct SSML with emotion and cadence inside <speechify:style>
    if emotion:
        ssml = (
            f'<speak xmlns:speechify="http://www.speechify.com/ssml">'
            f'<speechify:style emotion="{emotion}" rate="{rate}">'
            f'{safe_text}'
            f'</speechify:style>'
            f'</speak>'
        )
    else:
        ssml = f"<speak>{safe_text}</speak>"
    
        

    data = {
        "input": ssml,
        "voice_id": voice_id,
        "audio_format": "mp3",
        "ssml": True  # Crucial to activate SSML processing
    }

    response = requests.post("https://api.sws.speechify.com/v1/audio/speech", headers=headers, json=data)

    if response.status_code == 200:
        audio_data = base64.b64decode(response.json().get("audio_data"))
        output_path = os.path.join("data/Generated_Audio", user_id)
        os.makedirs(output_path, exist_ok=True)
        full_path = os.path.join(output_path, f"{file_name}.mp3")
        with open(full_path, "wb") as f:
            f.write(audio_data)
        return full_path
    else:
        print("❌ API Error:", response.status_code)
        print("Response:", response.text)
        return None

def build_ssml(text, rate="medium", pitch="medium", volume="medium"):
    return f'<speak><prosody rate="{rate}" pitch="{pitch}" volume="{volume}">{text}</prosody></speak>'

def generate_preview_audio(voice_id, text, rate, pitch, volume, emotion):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    ssml = build_ssml(xml_escape.escape(text), rate, pitch, volume)
    data = {
        "ssml": ssml,
        "voice_id": voice_id,
        "voice_settings": {"emotion": emotion}
    }
    r = requests.post("https://api.sws.speechify.com/v1/audio/stream", headers=headers, json=data)
    
    print("🔁 Preview Status:", r.status_code)
    print("▶️ Response Content:", r.content[:100])  # chỉ in thử vài byte
    print("📝 Payload:", data)

    return r.content if r.status_code == 200 else None


# Hàm generate full podcast
def generate_full_audio_and_upload(voice_id, text, rate, pitch, volume, emotion, filename):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    ssml = build_ssml(xml_escape.escape(text), rate, pitch, volume)

    data = {
        "ssml": ssml,
        "voice_id": voice_id,
        "audio_format": "mp3",
        "voice_settings": {"emotion": emotion}
    }

    response = requests.post("https://api.sws.speechify.com/v1/audio/speech", headers=headers, json=data)

    if response.status_code == 200:
        audio_data = base64.b64decode(response.json().get("audio_data"))
        output_path = f"data/Generated_Audio/{filename}.mp3"
        with open(output_path, "wb") as f:
            f.write(audio_data)

        from utils.cloudinary_utils import upload_audio_to_cloudinary
        cloud_url = upload_audio_to_cloudinary(output_path, folder="Generated_Audio", public_id=filename)

        return cloud_url, output_path
    else:
        print("❌ Full Generation Error:", response.status_code)
        print("Response:", response.text)
        return None, None

