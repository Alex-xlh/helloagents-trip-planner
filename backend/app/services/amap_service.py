"""高德地图MCP服务封装 (LangChain生态)"""

import os
import asyncio
import contextlib
from typing import List, Dict, Any, Optional
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# MCP 长连接缓存池
_mcp_pool = None
_mcp_pool_initialized = False
_mcp_exit_stack = contextlib.AsyncExitStack()
_mcp_init_lock = asyncio.Lock()

async def init_mcp_client():
    """初始化全局MCP客户端并发连接池并保持长连接"""
    global _mcp_pool, _mcp_pool_initialized
    
    # 第一次检查（无锁快速返回）
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


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    async def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """搜索POI"""
        try:
            result = await _call_mcp_tool_async("maps_text_search", {
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower()
            })
            print(f"POI搜索结果: {result[:200]}...")
            
            import json
            import re
            
            parsed_pois = []
            # 利用正则从原始文本中提取出干净的JSON结构
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    pois_data = data.get("pois", [])
                    
                    for p in pois_data:
                        # 高德返回的经纬度通常是字符串 "116.397,39.918"
                        loc_str = str(p.get("location", ""))
                        if loc_str and "," in loc_str:
                            lng, lat = loc_str.split(",", 1)
                            loc_obj = Location(longitude=float(lng), latitude=float(lat))
                            
                            poi_info = POIInfo(
                                id=str(p.get("id", "")),
                                name=str(p.get("name", "")),
                                type=str(p.get("type", "")),
                                address=str(p.get("address", "")),
                                location=loc_obj,
                                tel=str(p.get("tel", "")) if p.get("tel") else None
                            )
                            parsed_pois.append(poi_info)
                except Exception as parse_e:
                    print(f"⚠️ JSON解析或结构校验失败: {parse_e}")
                    
            return parsed_pois
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []
    
    async def get_weather(self, city: str) -> List[WeatherInfo]:
        """查询天气"""
        try:
            result = await _call_mcp_tool_async("maps_weather", {
                "city": city
            })
            print(f"天气查询结果: {result[:200]}...")
            
            import json
            import re
            
            parsed_weather = []
            # 提取干净的JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    # 高德天气API通常返回 forecasts 数组（包含未来几天预报）
                    forecasts = data.get("forecasts", [])
                    if forecasts and isinstance(forecasts, list) and len(forecasts) > 0:
                        casts = forecasts[0].get("casts", [])
                        for c in casts:
                            weather_info = WeatherInfo(
                                date=str(c.get("date", "")),
                                day_weather=str(c.get("dayweather", "")),
                                night_weather=str(c.get("nightweather", "")),
                                day_temp=str(c.get("daytemp", "0")),
                                night_temp=str(c.get("nighttemp", "0")),
                                wind_direction=str(c.get("daywind", "")),
                                wind_power=str(c.get("daypower", ""))
                            )
                            parsed_weather.append(weather_info)
                    else:
                        # 兜底：如果是实时天气(lives)
                        lives = data.get("lives", [])
                        if lives and isinstance(lives, list) and len(lives) > 0:
                            live = lives[0]
                            from datetime import date
                            weather_info = WeatherInfo(
                                date=date.today().strftime("%Y-%m-%d"),
                                day_weather=str(live.get("weather", "")),
                                night_weather=str(live.get("weather", "")),
                                day_temp=str(live.get("temperature", "0")),
                                night_temp=str(live.get("temperature", "0")),
                                wind_direction=str(live.get("winddirection", "")),
                                wind_power=str(live.get("windpower", ""))
                            )
                            parsed_weather.append(weather_info)
                            
                except Exception as parse_e:
                    print(f"⚠️ 天气JSON解析失败: {parse_e}")
                    
            return parsed_weather
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []
    
    async def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """规划路线"""
        try:
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }
            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
            
            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }
            if route_type == "transit":
                if origin_city: arguments["origin_city"] = origin_city
                if destination_city: arguments["destination_city"] = destination_city
            else:
                if origin_city: arguments["origin_city"] = origin_city
                if destination_city: arguments["destination_city"] = destination_city
            
            result = await _call_mcp_tool_async(tool_name, arguments)
            print(f"路线规划结果: {result[:200]}...")
            
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    route = data.get("route", {})
                    
                    distance = 0.0
                    duration = 0
                    
                    # 步行或驾车数据在 paths 里
                    paths = route.get("paths", [])
                    # 公交数据在 transits 里
                    transits = route.get("transits", [])
                    
                    if paths and len(paths) > 0:
                        distance = float(paths[0].get("distance", 0))
                        duration = int(paths[0].get("duration", 0))
                    elif transits and len(transits) > 0:
                        distance = float(transits[0].get("distance", 0))
                        duration = int(transits[0].get("duration", 0))
                        
                    # 生成一句人性化的描述
                    minutes = duration // 60
                    kms = distance / 1000
                    desc_map = {"walking": "步行", "driving": "驾车", "transit": "公交/地铁"}
                    desc = f"{desc_map.get(route_type, '出行')}总距离约 {kms:.1f} 公里，预计耗时 {minutes} 分钟。"
                    
                    return {
                        "distance": distance,
                        "duration": duration,
                        "route_type": route_type,
                        "description": desc
                    }
                except Exception as parse_e:
                    print(f"⚠️ 路线JSON解析失败: {parse_e}")
                    
            return None
        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return None
    
    async def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """地理编码(地址转坐标)"""
        try:
            arguments = {"address": address}
            if city: arguments["city"] = city
            result = await _call_mcp_tool_async("maps_geo", arguments)
            print(f"地理编码结果: {result[:200]}...")
            
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    geocodes = data.get("geocodes", [])
                    
                    if geocodes and len(geocodes) > 0:
                        loc_str = str(geocodes[0].get("location", ""))
                        if loc_str and "," in loc_str:
                            lng, lat = loc_str.split(",", 1)
                            return Location(longitude=float(lng), latitude=float(lat))
                            
                except Exception as parse_e:
                    print(f"⚠️ 地理编码JSON解析失败: {parse_e}")
                    
            return None
        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    async def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """获取POI详情"""
        try:
            result = await _call_mcp_tool_async("maps_search_detail", {
                "id": poi_id
            })
            print(f"POI详情结果: {result[:200]}...")
            import json
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw": result}
        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}

# 创建全局服务实例
_amap_service = None

def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    if _amap_service is None:
        _amap_service = AmapService()
    return _amap_service

# ==========================================
# 导出LangChain Tools
# ==========================================
from langchain_core.tools import tool

@tool
async def amap_maps_text_search(keywords: str, city: str) -> str:
    """根据关键词和城市搜索高德地图上的景点或酒店(POI)。返回相关信息的文本描述。"""
    raw_result = await _call_mcp_tool_async("maps_text_search", {"keywords": keywords, "city": city, "citylimit": "true"})
    
    import json
    import re
    # === 数据瘦身清洗层 ===
    json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            pois = data.get("pois", [])
            cleaned_pois = []
            
            # 扩大截断上限，保留前30条数据，为长途旅行提供充足弹药
            for p in pois[:30]:
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

                cleaned_pois.append({
                    "名称": p.get("name", ""),
                    "地址": p.get("address", ""),
                    "类型": p.get("type", "").split(";")[0] if p.get("type") else "", # 仅取主类型
                    "评分": rating,
                    "价格": cost,
                    "坐标": p.get("location", "")
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
    
    import json
    import re
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
