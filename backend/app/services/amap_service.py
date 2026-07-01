"""高德地图MCP服务封装 (LangChain生态)"""

import os
import asyncio
import contextlib
import json
import re
from typing import List, Dict, Any, Optional
from ..config import get_settings

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# MCP 长连接缓存池
_mcp_pool = None
_mcp_pool_initialized = False
_mcp_exit_stack = contextlib.AsyncExitStack()
#并发防盗锁
_mcp_init_lock = asyncio.Lock()

async def init_mcp_client():
    """初始化全局MCP客户端并发连接池并保持长连接"""
    global _mcp_pool, _mcp_pool_initialized
    
    # 第一次检查（无锁快速返回）防御性编程
    if _mcp_pool_initialized:
        return
        
    async with _mcp_init_lock:
        # 第二次检查（获取锁后再次确认，防止并发穿透）
        if _mcp_pool_initialized:
            return
            
        print("🔄 正在初始化 MCP 并发连接池 (容量: 3)...")
        settings = get_settings()
        if not settings.amap_api_key:
            raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")
            
        env = os.environ.copy()
        env["AMAP_MAPS_API_KEY"] = settings.amap_api_key

        command_name = "uvx.exe" if os.name == 'nt' else "uvx"
        server_params = StdioServerParameters(
            command=command_name,
            args=["--offline", "amap-mcp-server"],
            env=env
        )
        
        try:
            _mcp_pool = asyncio.Queue()
            POOL_SIZE = 3
            
            for i in range(POOL_SIZE):
                print(f"  - 正在启动 Node.js MCP 进程 {i+1}/{POOL_SIZE} ...")
                # 建立持久化的进程和管道上下文
                transport = await _mcp_exit_stack.enter_async_context(stdio_client(server_params))
                read, write = transport
                
                # 建立持久化的Session会话上下文
                session = await _mcp_exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                # 放入连接池
                await _mcp_pool.put(session)
                
            _mcp_pool_initialized = True
            print("✅ MCP 并发连接池拉起成功！(彻底消除单通道死锁，实现物理并发)")
        except Exception as e:
            print(f"❌ 初始化 MCP 长连接池失败: {e}")
            await _mcp_exit_stack.aclose()
            _mcp_pool_initialized = False
            raise

async def close_mcp_client():
    """安全释放MCP长连接"""
    global _mcp_pool, _mcp_pool_initialized
    print("🧹 正在释放 MCP 连接池资源...")
    await _mcp_exit_stack.aclose()
    _mcp_pool = None
    _mcp_pool_initialized = False
    print("✅ MCP 资源已安全回收。")

async def _call_mcp_tool_async(tool_name: str, arguments: dict) -> str:
    """使用MCP SDK异步调用工具(从连接池中获取)"""
    if not _mcp_pool_initialized:
        print("⚠️ 检测到 MCP 连接池尚未建立，正在进行临时初始化...")
        await init_mcp_client()
        
    # 从连接池中借用一个通道（如果满了则挂起等待）
    session = await _mcp_pool.get()
    try:
        # 物理并发调用，互不干扰
        result = await session.call_tool(tool_name, arguments=arguments)
    finally:
        # 用完后必须归还给连接池，否则池子会枯竭
        await _mcp_pool.put(session)
    
    if result.content:
        # 提取纯文本内容
        return "\n".join([c.text for c in result.content if hasattr(c, 'text')])
    return str(result)

# #异步转同步
# def call_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
#     """同步封装调用MCP工具"""
#     try:
#         # 创建新的事件循环，避免运行中事件循环报错
#         try:
#             loop = asyncio.get_event_loop()
#         except RuntimeError:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             
#         if loop.is_running():
#             import nest_asyncio
#             nest_asyncio.apply()
#             
#         return loop.run_until_complete(_call_mcp_tool_async(tool_name, arguments))
#     except Exception as e:
#         print(f"❌ MCP工具 {tool_name} 调用失败: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return str(e)




# ==========================================
# 导出LangChain Tools
# ==========================================
from langchain_core.tools import tool
import urllib.parse
from ..core.http_client import get_http_client
from ..config import get_settings

@tool
async def amap_maps_text_search(keywords: str, city: str, limit: int = 30) -> str:
    """根据关键词和城市搜索高德地图上的景点或酒店(POI)。返回相关信息的文本描述。"""
    raw_result = await _call_mcp_tool_async("maps_text_search", {"keywords": keywords, "city": city, "citylimit": "true"})
    
    # === 数据瘦身清洗层 ===
    json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            pois = data.get("pois", [])
            cleaned_pois = []
            
            # 根据传入的 limit 动态截断数据，防止精准搜索时 Token 爆炸
            pois = pois[:limit]
            
            settings = get_settings()
            amap_key = settings.amap_api_key
            http_client = get_http_client()

            async def fetch_precise_location(poi_name: str, fallback_loc: str) -> str:
                if not poi_name or not amap_key:
                    return fallback_loc
                try:
                    url = f"https://restapi.amap.com/v3/place/text?keywords={urllib.parse.quote(poi_name)}&city={urllib.parse.quote(city)}&key={amap_key}"
                    resp = await http_client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        api_data = resp.json()
                        api_pois = api_data.get("pois", [])
                        if api_pois and len(api_pois) > 0:
                            return api_pois[0].get("location", fallback_loc)
                except Exception as e:
                    print(f"⚠️ 高德原生 API 坐标纠偏失败({poi_name}): {e}")
                return fallback_loc

            # 并发获取精准坐标
            loc_tasks = [fetch_precise_location(p.get("name", ""), p.get("location", "")) for p in pois]
            precise_locations = await asyncio.gather(*loc_tasks)

            for i, p in enumerate(pois):
                biz_ext = p.get("biz_ext", {})
                
                # 提取评分和价格
                rating = "暂无"
                cost = "暂无"
                if isinstance(biz_ext, dict):
                    rating = biz_ext.get("rating", "暂无")
                    cost = biz_ext.get("cost", "暂无")
                elif isinstance(biz_ext, list) and len(biz_ext) > 0 and isinstance(biz_ext[0], dict):
                    rating = biz_ext[0].get("rating", "暂无")
                    cost = biz_ext[0].get("cost", "暂无")
                
                loc_val = precise_locations[i]


                cleaned_pois.append({
                    "名称": p.get("name", ""),
                    "地址": p.get("address", ""),
                    "类型": p.get("type", "").split(";")[0] if p.get("type") else "", # 仅取主类型
                    "评分": rating,
                    "价格": cost,
                    "坐标": loc_val
                })
            # 返回极简JSON，禁用了ASCII以减少Unicode转义的Token开销
            return json.dumps(cleaned_pois, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ POI数据清洗失败: {e}")
            return raw_result
    return raw_result

@tool
async def amap_maps_weather(city: str) -> str:
    """查询指定城市的天气信息。返回近期天气的文本描述。"""
    raw_result = await _call_mcp_tool_async("maps_weather", {"city": city})
    # === 数据瘦身清洗层 ===
    json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            forecasts = data.get("forecasts", [])
            cleaned_weather = []
            
            if forecasts and len(forecasts) > 0:
                casts = forecasts[0].get("casts", [])
                for c in casts:
                    cleaned_weather.append({
                        "日期": c.get("date", ""),
                        "白天天气": c.get("dayweather", ""),
                        "夜间天气": c.get("nightweather", ""),
                        "白天温度": c.get("daytemp", ""),
                        "夜间温度": c.get("nighttemp", "")
                    })
            return json.dumps(cleaned_weather, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 天气数据清洗失败: {e}")
            return raw_result
    return raw_result
