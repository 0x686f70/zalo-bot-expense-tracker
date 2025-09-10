import google.generativeai as genai
import os
import logging
from typing import Optional
import json
from services.api_key_manager import APIKeyManager

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service tích hợp Gemini AI với multiple API keys rotation"""
    
    def __init__(self):
        self.api_manager = APIKeyManager()
        self.model = None
        self.current_api_key = None
        self.enabled = False
        
        if self.api_manager.has_available_keys():
            self._initialize_with_current_key()
        else:
            logger.warning("⚠️  Không có API key khả dụng - tính năng AI sẽ bị vô hiệu hóa")
    
    def _initialize_with_current_key(self):
        """Khởi tạo Gemini với API key hiện tại"""
        try:
            api_key = self.api_manager.get_current_api_key()
            if not api_key:
                self.enabled = False
                return
            
            # Chỉ configure lại nếu key khác
            if api_key != self.current_api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.current_api_key = api_key
                
                key_index = self.api_manager.api_keys.index(api_key) + 1
                logger.info(f"🔑 Gemini AI khởi tạo với API Key {key_index}")
            
            self.enabled = True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khởi tạo Gemini AI: {e}")
            self.enabled = False
    
    def categorize_expense(self, description: str) -> str:
        """
        Phân loại khoản chi dựa trên mô tả
        
        Args:
            description: Mô tả khoản chi (VD: "trà sữa", "đổ xăng", "mua áo")
            
        Returns:
            str: Danh mục được phân loại
        """
        if not self.enabled:
            return "Khác"
        
        try:
            prompt = f"""
Hãy phân loại khoản chi tiêu sau vào một trong các danh mục phù hợp nhất:

Mô tả: "{description}"

Danh sách danh mục có sẵn:
- Ăn uống: đồ ăn, thức uống, nhà hàng, quán cà phê, trà sữa, bánh kẹo, nướng, luộc, xào, chiên, thịt, cá, gà, rau, củ, quả
- Di chuyển: xăng xe, vé xe buýt, taxi, grab, đi lại, gửi xe, tiền xe, phí đường
- Mua sắm: quần áo, giày dép, đồ dùng, mỹ phẩm, điện tử, laptop, điện thoại
- Giải trí: xem phim, game, du lịch, karaoke, bar, concert, show
- Y tế: thuốc, khám bệnh, nha khoa, bảo hiểm y tế, xét nghiệm
- Học tập: sách vở, khóa học, học phí, văn phòng phẩm, giáo dục
- Nhà cửa: tiền nhà, điện nước, internet, sửa chữa, gas, wifi
- Khác: những thứ THỰC SỰ không thuộc 7 danh mục trên

QUAN TRỌNG: "nướng", "luộc", "xào", "chiên" = NẤU ĂN → Ăn uống

Chỉ trả về TÊN DANH MỤC, không giải thích gì thêm.
"""
            
            response = self.model.generate_content(prompt)
            category = response.text.strip()
            
            # Validate danh mục trả về
            valid_categories = [
                "Ăn uống", "Di chuyển", "Mua sắm", "Giải trí", 
                "Y tế", "Học tập", "Nhà cửa", "Khác"
            ]
            
            if category in valid_categories:
                logger.info(f"AI phân loại '{description}' -> '{category}'")
                return category
            else:
                logger.warning(f"AI trả về danh mục không hợp lệ: {category}")
                return "Khác"
                
        except Exception as e:
            logger.error(f"Lỗi phân loại AI: {e}")
            return "Khác"
    
    def categorize_income(self, description: str) -> str:
        """
        Phân loại khoản thu dựa trên mô tả
        
        Args:
            description: Mô tả khoản thu (VD: "lương", "bán hàng", "thưởng")
            
        Returns:
            str: Danh mục được phân loại
        """
        if not self.enabled:
            return "Khác"
        
        try:
            prompt = f"""
Hãy phân loại khoản thu nhập sau vào một trong các danh mục phù hợp nhất:

Mô tả: "{description}"

Danh sách danh mục có sẵn:
- Lương: lương tháng, lương cơ bản, phụ cấp
- Thưởng: thưởng tết, thưởng dự án, thưởng hiệu suất
- Freelance: làm thêm, dự án cá nhân, part-time
- Bán hàng: bán đồ, kinh doanh nhỏ lẻ
- Đầu tư: cổ tức, lãi suất, crypto, chứng khoán
- Khác: những khoản thu khác

Chỉ trả về TÊN DANH MỤC, không giải thích gì thêm.
"""
            
            response = self.model.generate_content(prompt)
            category = response.text.strip()
            
            # Validate danh mục trả về
            valid_categories = [
                "Lương", "Thưởng", "Freelance", "Bán hàng", "Đầu tư", "Khác"
            ]
            
            if category in valid_categories:
                logger.info(f"AI phân loại '{description}' -> '{category}'")
                return category
            else:
                logger.warning(f"AI trả về danh mục không hợp lệ: {category}")
                return "Khác"
                
        except Exception as e:
            logger.error(f"Lỗi phân loại AI: {e}")
            return "Khác"
    
    def is_enabled(self) -> bool:
        """Kiểm tra AI có được bật không"""
        return self.enabled
    
    def get_api_status(self) -> dict:
        """Lấy trạng thái tất cả API keys"""
        return self.api_manager.get_status()
    
    def get_current_key_info(self) -> str:
        """Lấy thông tin API key hiện tại"""
        if not self.current_api_key:
            return "Không có API key"
        
        try:
            key_index = self.api_manager.api_keys.index(self.current_api_key) + 1
            return f"API Key {key_index} ({self.current_api_key[:20]}...)"
        except:
            return "Unknown key"
    
    def _generate_content(self, prompt: str) -> str:
        """Helper method để generate content với auto key rotation"""
        if not self.enabled:
            return ""
        
        max_retries = len(self.api_manager.api_keys) if self.api_manager.api_keys else 1
        
        for attempt in range(max_retries):
            try:
                # Đảm bảo có API key khả dụng
                if not self.api_manager.has_available_keys():
                    logger.warning("⚠️  Tất cả API keys đều trong cooldown")
                    break
                
                # Reinitialize nếu cần
                self._initialize_with_current_key()
                
                if not self.enabled or not self.model:
                    break
                
                # Thử generate content
                response = self.model.generate_content(prompt)
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"🚫 Lỗi generate content (attempt {attempt + 1}): {error_msg}")
                
                # Đánh dấu key hiện tại failed và rotate
                if self.current_api_key:
                    self.api_manager.mark_key_failed(self.current_api_key, error_msg)
                
                # Nếu không phải lỗi quota, không retry
                is_quota_error = any(keyword in error_msg.lower() for keyword in [
                    '429', 'quota', 'rate limit', 'exceeded', 'resource_exhausted'
                ])
                
                if not is_quota_error:
                    raise e
                
                # Thử key tiếp theo
                continue
        
        # Hết tất cả attempts
        logger.error("❌ Đã thử hết tất cả API keys")
        raise Exception("All API keys exhausted")