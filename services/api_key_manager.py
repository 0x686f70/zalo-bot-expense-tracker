import os
import logging
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Quản lý multiple API keys với auto rotation khi hết quota"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.failed_keys = {}  # Track failed keys with timestamp
        self.cooldown_minutes = 30  # Cooldown time for failed keys (optimized for 150/day)
        
        logger.info(f"🔑 Loaded {len(self.api_keys)} API keys")
    
    def _load_api_keys(self) -> List[str]:
        """Load API keys từ environment variables"""
        keys = []
        
        # Method 1: Single key (backward compatibility)
        single_key = os.getenv('GEMINI_API_KEY')
        if single_key:
            keys.append(single_key.strip())
        
        # Method 2: Multiple keys (comma separated)
        multi_keys = os.getenv('GEMINI_API_KEYS')
        if multi_keys:
            for key in multi_keys.split(','):
                key = key.strip()
                if key and key not in keys:
                    keys.append(key)
        
        # Method 3: Numbered keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...)
        i = 1
        while True:
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if not key:
                break
            key = key.strip()
            if key and key not in keys:
                keys.append(key)
            i += 1
        
        if not keys:
            logger.warning("⚠️  Không tìm thấy API key nào")
        
        return keys
    
    def get_current_api_key(self) -> Optional[str]:
        """Lấy API key hiện tại (có thể sử dụng được)"""
        if not self.api_keys:
            return None
        
        # Thử từ key hiện tại
        for attempt in range(len(self.api_keys)):
            key_index = (self.current_key_index + attempt) % len(self.api_keys)
            key = self.api_keys[key_index]
            
            # Kiểm tra key có trong cooldown không
            if self._is_key_in_cooldown(key):
                logger.debug(f"🕒 API Key {key_index + 1} đang trong cooldown")
                continue
            
            # Cập nhật current index
            if key_index != self.current_key_index:
                self.current_key_index = key_index
                logger.info(f"🔄 Chuyển sang API Key {key_index + 1}")
            
            return key
        
        # Tất cả keys đều trong cooldown
        logger.warning("⏰ Tất cả API keys đang trong cooldown")
        return self.api_keys[self.current_key_index]  # Return current anyway
    
    def mark_key_failed(self, api_key: str, error_message: str = ""):
        """Đánh dấu API key bị lỗi và chuyển sang key khác"""
        if api_key not in self.api_keys:
            return
        
        key_index = self.api_keys.index(api_key) + 1
        
        # Check if it's a quota/rate limit error
        is_quota_error = any(keyword in error_message.lower() for keyword in [
            '429', 'quota', 'rate limit', 'exceeded', 'resource_exhausted'
        ])
        
        if is_quota_error:
            # Mark key as failed with timestamp
            self.failed_keys[api_key] = datetime.now()
            logger.warning(f"🚫 API Key {key_index} hết quota - đánh dấu cooldown {self.cooldown_minutes} phút")
            
            # Rotate to next key
            self._rotate_to_next_key()
        else:
            logger.error(f"❌ API Key {key_index} lỗi: {error_message[:100]}")
    
    def _rotate_to_next_key(self):
        """Chuyển sang API key tiếp theo"""
        if len(self.api_keys) <= 1:
            return
        
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        logger.info(f"🔄 Rotation: Key {old_index + 1} → Key {self.current_key_index + 1}")
    
    def _is_key_in_cooldown(self, api_key: str) -> bool:
        """Kiểm tra API key có đang trong cooldown không"""
        if api_key not in self.failed_keys:
            return False
        
        failed_time = self.failed_keys[api_key]
        cooldown_until = failed_time + timedelta(minutes=self.cooldown_minutes)
        
        if datetime.now() >= cooldown_until:
            # Cooldown ended, remove from failed list
            del self.failed_keys[api_key]
            key_index = self.api_keys.index(api_key) + 1
            logger.info(f"✅ API Key {key_index} đã hết cooldown - có thể sử dụng lại")
            return False
        
        return True
    
    def get_status(self) -> Dict:
        """Lấy trạng thái của tất cả API keys"""
        status = {
            'total_keys': len(self.api_keys),
            'current_key_index': self.current_key_index + 1,
            'available_keys': 0,
            'cooldown_keys': 0,
            'keys_status': []
        }
        
        for i, key in enumerate(self.api_keys):
            key_status = {
                'index': i + 1,
                'key_preview': f"{key[:20]}..." if key else "None",
                'status': 'available',
                'is_current': i == self.current_key_index
            }
            
            if self._is_key_in_cooldown(key):
                key_status['status'] = 'cooldown'
                failed_time = self.failed_keys[key]
                remaining = failed_time + timedelta(minutes=self.cooldown_minutes) - datetime.now()
                key_status['cooldown_remaining'] = f"{int(remaining.total_seconds() // 60)}m"
                status['cooldown_keys'] += 1
            else:
                status['available_keys'] += 1
            
            status['keys_status'].append(key_status)
        
        return status
    
    def has_available_keys(self) -> bool:
        """Kiểm tra có API key nào khả dụng không"""
        return len(self.api_keys) > 0 and any(
            not self._is_key_in_cooldown(key) for key in self.api_keys
        ) 