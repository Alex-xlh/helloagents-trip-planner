"""POI相关API路由"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from ...config import get_settings
from ...core.http_client import get_http_client

router = APIRouter(prefix="/poi", tags=["POI"])
settings = get_settings()


@router.get(
    "/photo",
    summary="获取景点图片",
    description="根据景点名称从高德获取图片"
)
async def get_attraction_photo(name: str, city: Optional[str] = None):
    """
    获取景点图片

    Args:
        name: 景点名称
        city: 城市名称（可选，用于限定搜索范围）

    Returns:
        图片URL
    """
    try:
        api_key = settings.amap_api_key
        
        photo_url = None
        
        if api_key:
            # 调用高德POI搜索API获取图片
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                "keywords": name,
                "key": api_key,
                "extensions": "all",  # 需要设置为all才能获取深度信息(含图片)
                "offset": 5,          # 获取前5个结果，增加命中率
                "page": 1
            }
            if city:
                params["city"] = city
            
            client = get_http_client()
            response = await client.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1" and data.get("pois"):
                    # 遍历前5个POI，寻找任何一个带有图片的POI
                    for poi in data["pois"]:
                        photos = poi.get("photos", [])
                        if photos and isinstance(photos, list) and len(photos) > 0:
                            # 过滤掉不存在的或空的URL
                            valid_photos = [p for p in photos if isinstance(p, dict) and p.get("url")]
                            if valid_photos:
                                photo_url = valid_photos[0]["url"]
                                break # 找到第一张有效的图片就立刻跳出循环


        return {
            "success": True,
            "message": "获取图片成功",
            "data": {
                "name": name,
                "photo_url": photo_url
            }
        }

    except Exception as e:
        print(f"❌ 获取景点图片失败: {str(e)}")
        # 为了不影响前端，这里不要抛出500，直接返回null图片
        return {
            "success": True,
            "message": f"获取景点图片失败: {str(e)}",
            "data": {
                "name": name,
                "photo_url": None
            }
        }


