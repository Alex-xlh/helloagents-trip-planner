"""高德地图MCP服务封装 (LangChain生态)"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# 缓存MCP客户端上下文
_mcp_session_context = None

async def _call_mcp_tool_async(tool_name: str, arguments: dict) -> str:
    """使用MCP SDK异步调用工具"""
    settings = get_settings()
    if not settings.amap_api_key:
        raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")

    # 复制环境变量并更新
    env = os.environ.copy()
    env["AMAP_MAPS_API_KEY"] = settings.amap_api_key

    command_name = "uvx.exe" if os.name == 'nt' else "uvx"
    server_params = StdioServerParameters(
        command=command_name,
        args=["amap-mcp-server"],
        env=env
    )
    
    # 由于这是一个独立的短连接调用，直接创建session并在结束时关闭
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            if result.content:
                # 提取纯文本内容
                return "\n".join([c.text for c in result.content if hasattr(c, 'text')])
            return str(result)


def call_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
    """同步封装调用MCP工具"""
    try:
        # 创建新的事件循环，避免运行中事件循环报错
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            
        return loop.run_until_complete(_call_mcp_tool_async(tool_name, arguments))
    except Exception as e:
        print(f"❌ MCP工具 {tool_name} 调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return str(e)


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """搜索POI"""
        try:
            result = call_mcp_tool_sync("maps_text_search", {
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower()
            })
            print(f"POI搜索结果: {result[:200]}...")
            # TODO: 解析实际的POI数据
            return []
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """查询天气"""
        try:
            result = call_mcp_tool_sync("maps_weather", {
                "city": city
            })
            print(f"天气查询结果: {result[:200]}...")
            return []
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []
    
    def plan_route(
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
            
            result = call_mcp_tool_sync(tool_name, arguments)
            print(f"路线规划结果: {result[:200]}...")
            return {}
        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """地理编码(地址转坐标)"""
        try:
            arguments = {"address": address}
            if city: arguments["city"] = city
            result = call_mcp_tool_sync("maps_geo", arguments)
            print(f"地理编码结果: {result[:200]}...")
            return None
        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """获取POI详情"""
        try:
            result = call_mcp_tool_sync("maps_search_detail", {
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
def amap_maps_text_search(keywords: str, city: str) -> str:
    """根据关键词和城市搜索高德地图上的景点或酒店(POI)。返回相关信息的文本描述。"""
    return call_mcp_tool_sync("maps_text_search", {"keywords": keywords, "city": city, "citylimit": "true"})

@tool
def amap_maps_weather(city: str) -> str:
    """查询指定城市的天气信息。返回近期天气的文本描述。"""
    return call_mcp_tool_sync("maps_weather", {"city": city})
