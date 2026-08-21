"""LLM服务模块"""

import os
from langchain_openai import ChatOpenAI
from ..config import get_settings

# 全局LLM实例
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """
    获取LLM实例(单例模式)
    
    Returns:
        ChatOpenAI实例
    """
    global _llm_instance
    
    if _llm_instance is None:
        settings = get_settings()
        
        # 直接从环境变量读取
        llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL")
        llm_model = os.getenv("LLM_MODEL_ID")
        llm_timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        
        if not llm_api_key:
            print("⚠️ 未配置 API KEY, LLM 可能会调用失败")

        model_kwargs = {
            "api_key": llm_api_key,
            "base_url": llm_base_url,
            "model": llm_model,
            "temperature": 0.7,
            "timeout": llm_timeout,
        }
        if llm_base_url and "deepseek" in llm_base_url.lower():
            model_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        _llm_instance = ChatOpenAI(
            **model_kwargs
        )
        
        print(f"✅ LLM服务初始化成功(LangChain)")
        print(f"   模型: {llm_model}")
        print(f"   思考模式: {'关闭' if model_kwargs.get('extra_body') else '默认'}")
    
    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None
