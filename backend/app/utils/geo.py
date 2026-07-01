import math

def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    计算地球上两点间的球面真实距离（千米）
    """
    R = 6371.0 # 地球平均半径，单位：公里
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

