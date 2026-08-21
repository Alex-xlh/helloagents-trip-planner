import os
import uuid
import time
from pathlib import Path
import edge_tts
from pydantic import BaseModel
from loguru import logger
from ..config import get_settings

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"

def cleanup_expired_tts_files() -> int:
    """删除过期 TTS 音频缓存文件。"""
    settings = get_settings()
    max_age_seconds = max(1, settings.tts_max_age_hours) * 3600
    cutoff = time.time() - max_age_seconds
    tts_dir = Path("static/tts")
    if not tts_dir.exists():
        return 0

    deleted = 0
    for file_path in tts_dir.glob("*.mp3"):
        try:
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                deleted += 1
        except OSError as e:
            logger.warning(f"TTS缓存清理失败({file_path.name}): {e}")
    return deleted
    
async def generate_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """
    Generates TTS audio and saves it to static/tts/ directory.
    Returns the relative URL to the audio file.
    """
    # Create directory if it doesn't exist
    os.makedirs("static/tts", exist_ok=True)
    deleted_count = cleanup_expired_tts_files()
    if deleted_count:
        logger.info(f"已清理过期TTS音频: {deleted_count}个")
    
    # Generate a unique filename
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join("static/tts", filename)
    
    # Run edge-tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)
    
    # Return the URL path
    return f"/static/tts/{filename}"
