import time
import json
from typing import Any, Optional, Dict

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class InMemoryCache:
    def __init__(self):
        self._data: Dict[str, tuple[str, Optional[float]]] = {} # key -> (serialized_value, expiry_timestamp)

    def get(self, key: str) -> Optional[str]:
        if key not in self._data:
            return None
        val, expiry = self._data[key]
        if expiry is not None and time.time() > expiry:
            del self._data[key]
            return None
        return val

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expiry = time.time() + ex if ex else None
        self._data[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def incr(self, key: str) -> int:
        val = self.get(key)
        if val is None:
            new_val = 1
        else:
            try:
                new_val = int(val) + 1
            except ValueError:
                new_val = 1
        
        # Keep original expiry if still present
        expiry_timestamp = None
        if key in self._data:
            _, expiry_timestamp = self._data[key]
            
        remaining_ttl = None
        if expiry_timestamp:
            remaining_ttl = int(expiry_timestamp - time.time())
            if remaining_ttl <= 0:
                remaining_ttl = None
                
        self.set(key, str(new_val), ex=remaining_ttl)
        return new_val

class CacheService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_client = None
        self.local_cache = InMemoryCache()
        self.use_redis = False

        if REDIS_AVAILABLE:
            try:
                # Use a 1.0 second socket timeout to prevent FastAPI blockage
                self.redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db, 
                    socket_timeout=1.0, 
                    decode_responses=True
                )
                self.redis_client.ping()
                self.use_redis = True
                print("CacheService: Redis connection established successfully.")
            except Exception as e:
                print(f"CacheService: Redis connection failed ({e}). Falling back to InMemoryCache.")
                self.use_redis = False
        else:
            print("CacheService: 'redis' package not installed. Running on InMemoryCache.")

    def get(self, key: str) -> Optional[Any]:
        if self.use_redis:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                print(f"Redis GET error: {e}")
        
        val = self.local_cache.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return val
        return None

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        ser_val = json.dumps(value)
        if self.use_redis:
            try:
                self.redis_client.set(key, ser_val, ex=expire_seconds)
                return True
            except Exception as e:
                print(f"Redis SET error: {e}")
        
        return self.local_cache.set(key, ser_val, ex=expire_seconds)

    def delete(self, key: str) -> bool:
        if self.use_redis:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                print(f"Redis DELETE error: {e}")
        return self.local_cache.delete(key)

    def incr_rate_limit(self, key: str, window_seconds: int = 60) -> int:
        if self.use_redis:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.ttl(key)
                res = pipe.execute()
                count = res[0]
                ttl = res[1]
                if ttl == -1:
                    self.redis_client.expire(key, window_seconds)
                return count
            except Exception as e:
                print(f"Redis INCR error: {e}")
        
        val = self.local_cache.get(key)
        if val is None:
            self.local_cache.set(key, "1", ex=window_seconds)
            return 1
        else:
            return self.local_cache.incr(key)

    def get_prompt(self, name: str, default_template: str) -> str:
        key = f"prompt:{name}"
        cached = self.get(key)
        if cached:
            return cached
        self.set(key, default_template, expire_seconds=3600)  # 1 hour TTL
        return default_template

cache_service = CacheService()
