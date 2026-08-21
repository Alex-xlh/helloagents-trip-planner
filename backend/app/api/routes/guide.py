from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from loguru import logger
from ...services.llm_service import get_llm
from ...core.limiter import limiter

router = APIRouter(tags=["guide"])

class GuideChatRequest(BaseModel):
    text: str
    history: Optional[List[dict]] = []
    
# System Prompt 赋予导游人设
GUIDE_SYSTEM_PROMPT = """
你现在是一个名叫 Shizuku 的二次元智能旅行向导，性格活泼、甜美可爱、热情好客。
你负责陪伴用户在网页上制定旅行计划。
请遵循以下规则回答用户：
1. 语气必须活泼可爱，可以适当地使用像“哇哦！”、“好耶！”、“嗯嗯~”这样的语气词。
2. 用户的提问通常是关于旅游、行程、或者对你的调侃。
3. **最重要**：你的回答将被直接送入语音合成引擎 (TTS) 播报。因此：
   - 每次回答请务必控制在 50 字以内，尽量简短精炼。
   - **绝对禁止**使用任何颜文字、Emoji表情符号（如 😊、(●'◡'●) 等）。
   - **绝对禁止**输出任何描写动作的词语（如 *蹦跳*、*开心*、[微笑]、*探头* 等）。
   - 只能输出纯净的中文文本和基础标点符号，不能有任何让语音引擎无法正常朗读的字符。
"""

@router.post("/guide/chat")
@limiter.limit("20/minute")
async def guide_chat(request: Request, guide_request: GuideChatRequest):
    """
    接收用户与虚拟导游的聊天内容，返回简短的 AI 语音文案
    """
    if not guide_request.text or not guide_request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        llm = get_llm()
        
        messages = [SystemMessage(content=GUIDE_SYSTEM_PROMPT)]
        
        # 拼接短期记忆 (上下文)
        if guide_request.history:
            # 限制最多携带最近的 10 条对话记录，避免上下文溢出
            recent_history = guide_request.history[-10:]
            for msg in recent_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                    
        # 拼接最新的提问
        messages.append(HumanMessage(content=guide_request.text))
        
        response = await llm.ainvoke(messages)
        
        return {"reply": response.content}
        
    except Exception as e:
        logger.exception(f"虚拟导游聊天失败: {e}")
        # 提供一个友好的降级回复，以防 LLM 调用失败（例如没配 API Key）
        return {"reply": "哎呀，我的大脑暂时断线了，请检查一下后端的模型配置哦~"}
