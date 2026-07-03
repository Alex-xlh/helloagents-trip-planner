import os
import uuid
import edge_tts
from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    
async def generate_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """
    Generates TTS audio and saves it to static/tts/ directory.
    Returns the relative URL to the audio file.
    """
    # Create directory if it doesn't exist
    os.makedirs("static/tts", exist_ok=True)
    
    # Generate a unique filename
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join("static/tts", filename)
    
    # Run edge-tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)
    
    # Return the URL path
    return f"/static/tts/{filename}"
