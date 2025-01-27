from collections import OrderedDict
from typing import Any, Optional
import time
from app.config.settings import settings

class LRUCache:
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
            
        self.cache.move_to_end(key)
        return value
    
    def set(self, key: str, value: Any):
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)

cache = LRUCache(
    max_size=settings.CACHE_MAX_SIZE,
    ttl=settings.CACHE_TTL
) 