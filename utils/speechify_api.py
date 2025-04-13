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

    # Escape text to avoid XML errors
    safe_text = xml_escape.escape(text)

    # Build SSML
    if emotion:
        ssml = f'''
            <speak xmlns:speechify="http://www.speechify.com/ssml">
                <speechify:style emotion="{emotion}" cadence="{rate}">
                    {safe_text}
                </speechify:style>
            </speak>
        '''
    else:
        ssml = f"<speak>{safe_text}</speak>"

    data = {
        "input": ssml,
        "voice_id": voice_id,
        "audio_format": "mp3",
        "ssml": True  # ✅ THIS MAKES EVERYTHING WORK
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
        print("❌ ERROR:", response.status_code, response.text)
        return None
