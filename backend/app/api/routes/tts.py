from fastapi import APIRouter, HTTPException
from ...services.tts_service import generate_tts, TTSRequest

router = APIRouter(tags=["tts"])

@router.post("/tts/generate")
async def generate_tts_endpoint(request: TTSRequest):
    """
    Generates TTS audio from text and returns the URL.
    """
    try:
        url = await generate_tts(request.text, request.voice)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
