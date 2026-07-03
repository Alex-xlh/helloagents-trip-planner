from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from ...services.llm_service import get_llm

router = APIRouter(tags=["guide"])

class GuideChatRequest(BaseModel):
    text: str
    
# System Prompt 赋予导游人设
GUIDE_SYSTEM_PROMPT = """
你现在是一个名叫 Shizuku 的二次元智能旅行向导，性格活泼、甜美可爱、热情好客。
你负责陪伴用户在网页上制定旅行计划。
请遵循以下规则回答用户：
1. 语气必须活泼可爱，可以适当地使用像“哇哦！”、“好耶！”、“嗯嗯~”这样的语气词。
2. 用户的提问通常是关于旅游、行程、或者对你的调侃。
3. **最重要**：你的回答将被转为语音播报，因此每次回答请务必控制在 50 字以内，尽量简短精炼，不要出现复杂的 markdown 格式（如表格、加粗符号等），只能输出纯文本和基础标点符号。
"""

@router.post("/guide/chat")
async def guide_chat(request: GuideChatRequest):
    """
    接收用户与虚拟导游的聊天内容，返回简短的 AI 语音文案
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        llm = get_llm()
        
        messages = [
            SystemMessage(content=GUIDE_SYSTEM_PROMPT),
            HumanMessage(content=request.text)
        ]
        
        response = await llm.ainvoke(messages)
        
        return {"reply": response.content}
        
    except Exception as e:
        print(f"[ERROR] Guide Chat Failed: {e}")
        # 提供一个友好的降级回复，以防 LLM 调用失败（例如没配 API Key）
        return {"reply": "哎呀，我的大脑暂时断线了，请检查一下后端的模型配置哦~"}
