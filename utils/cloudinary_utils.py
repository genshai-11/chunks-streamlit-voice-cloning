import cloudinary
import cloudinary.uploader

# Cloudinary Configuration
cloudinary.config(
    cloud_name="db2xejmzb",
    api_key="323161334698122",
    api_secret="11eCewgi_frSoOWsGLrhA5mPRWY",
    secure=True
)

def upload_audio_to_cloudinary(local_path, folder, public_id=None):
    try:
        response = cloudinary.uploader.upload(
            local_path,
            resource_type="video",  # audio treated as video
            public_id=public_id,
            folder=folder,  # ✅ dynamic folder
            overwrite=True
        )
        print(f"✅ Uploaded to Cloudinary: {response['secure_url']}")
        return response["secure_url"]
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        return None
