import time
from typing import Any, Dict

class Cache:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {}
            cls._instance.expire_time = 600  # 10分钟缓存
        return cls._instance
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def get(self, key: str) -> Any:
        if key not in self.data:
            return None
            
        cached = self.data[key]
        if time.time() - cached["timestamp"] > self.expire_time:
            del self.data[key]
            return None
            
        return cached["value"]

# 全局缓存实例
global_cache = Cache()
