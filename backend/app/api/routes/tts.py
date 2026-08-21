from fastapi import APIRouter, HTTPException, Request
from ...services.tts_service import generate_tts, TTSRequest
from ...core.limiter import limiter

router = APIRouter(tags=["tts"])

@router.post("/tts/generate")
@limiter.limit("20/minute")
async def generate_tts_endpoint(request: Request, tts_request: TTSRequest):
    """
    Generates TTS audio from text and returns the URL.
    """
    try:
        url = await generate_tts(tts_request.text, tts_request.voice)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
