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
    # Always include speechify namespace
    if emotion:
        ssml = (
            f'<speak xmlns:speechify="http://www.speechify.com/ssml">'
            f'<speechify:style emotion="{emotion}" rate="{rate}">'
            f'{safe_text}'
            f'</speechify:style>'
            f'</speak>'
        )
    else:
        ssml = (
            f'<speak xmlns:speechify="http://www.speechify.com/ssml">'
            f'<speechify:style rate="{rate}">'
            f'{safe_text}'
            f'</speechify:style>'
            f'</speak>'
        )

    data = {
        "input": ssml,
        "voice_id": voice_id,
        "audio_format": "mp3",
        "ssml": True
    }

    try:
        response = requests.post("https://api.sws.speechify.com/v1/audio/speech", headers=headers, json=data)
        response.raise_for_status()
        audio_data = base64.b64decode(response.json().get("audio_data"))

        # Sanitize file_name
        safe_file_name = re.sub(r'[^\w\-_\.]', '_', file_name)
        output_path = os.path.join("data", "Generated_Audio", user_id)
        os.makedirs(output_path, exist_ok=True)
        full_path = os.path.join(output_path, f"{safe_file_name}.mp3")

        with open(full_path, "wb") as f:
            f.write(audio_data)
        return full_path
    except requests.RequestException as e:
        print(f"❌ Audio Generation Error: {e}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")
        return None
