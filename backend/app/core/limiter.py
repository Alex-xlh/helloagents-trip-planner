from slowapi import Limiter
from slowapi.util import get_remote_address

# 初始化限流器：防止恶意用户脚本疯狂刷接口，把大模型的钱刷破产
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])
