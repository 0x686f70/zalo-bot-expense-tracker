import json
import os
import logging
import re
from typing import Optional, Dict
from services.google_sheets import GoogleSheetsService

logger = logging.getLogger(__name__)

class UserSheetManager:
    """Quản lý Google Sheet riêng cho từng user thông qua file mapping"""
    
    def __init__(self):
        self.user_sheets_file = "user_sheets.json"
        self.user_sheets = self._load_user_sheets()
        
    def _load_user_sheets(self) -> Dict[str, str]:
        """Load danh sách user sheets từ file JSON"""
        try:
            if os.path.exists(self.user_sheets_file):
                with open(self.user_sheets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📋 Loaded {len(data)} user sheets từ file")
                    return data
            else:
                logger.info("📄 Tạo file user_sheets.json mới")
                return {}
        except Exception as e:
            logger.error(f"❌ Lỗi load user sheets: {e}")
            return {}
    
    def _save_user_sheets(self):
        """Lưu danh sách user sheets vào file JSON"""
        try:
            with open(self.user_sheets_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_sheets, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Đã lưu {len(self.user_sheets)} user sheets")
        except Exception as e:
            logger.error(f"❌ Lỗi lưu user sheets: {e}")
    
    def _extract_sheet_id(self, sheet_url: str) -> Optional[str]:
        """Trích xuất Google Sheet ID từ URL"""
        try:
            # Pattern cho Google Sheets URL
            patterns = [
                r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
                r'[?&]id=([a-zA-Z0-9-_]+)',
                r'^([a-zA-Z0-9-_]{44})$'  # Direct sheet ID
            ]
            
            for pattern in patterns:
                match = re.search(pattern, sheet_url)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"❌ Lỗi extract sheet ID: {e}")
            return None
    
    def _validate_sheet_url(self, sheet_url: str) -> bool:
        """Kiểm tra xem Google Sheet URL có hợp lệ không"""
        try:
            sheet_id = self._extract_sheet_id(sheet_url)
            if not sheet_id:
                return False
            
            # Thử tạo GoogleSheetsService để test
            test_service = GoogleSheetsService()
            test_service.sheet_id = sheet_id
            
            # Override spreadsheet
            test_service.spreadsheet = test_service.client.open_by_key(sheet_id)
            
            # Thử test connection
            test_service.test_connection()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Sheet URL không hợp lệ: {e}")
            return False
    
    def has_user_sheet(self, user_id: str) -> bool:
        """Kiểm tra user đã có sheet chưa"""
        return user_id in self.user_sheets
    
    def get_user_sheet_url(self, user_id: str) -> Optional[str]:
        """Lấy Google Sheet URL của user"""
        return self.user_sheets.get(user_id)
    
    def add_user_sheet(self, user_id: str, user_name: str, sheet_url: str) -> bool:
        """Thêm Google Sheet cho user"""
        try:
            # Validate URL trước
            if not self._validate_sheet_url(sheet_url):
                logger.error(f"❌ Sheet URL không hợp lệ cho user {user_name}")
                return False
            
            # Lưu vào mapping
            self.user_sheets[user_id] = sheet_url
            self._save_user_sheets()
            
            logger.info(f"✅ Đã thêm sheet cho user {user_name} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi thêm user sheet: {e}")
            return False
    
    def remove_user_sheet(self, user_id: str) -> bool:
        """Xóa Google Sheet của user"""
        try:
            if user_id in self.user_sheets:
                del self.user_sheets[user_id]
                self._save_user_sheets()
                logger.info(f"🗑️ Đã xóa sheet cho user ID: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Lỗi xóa user sheet: {e}")
            return False
    
    def get_user_service(self, user_id: str) -> Optional[GoogleSheetsService]:
        """Tạo GoogleSheetsService riêng cho user"""
        try:
            sheet_url = self.get_user_sheet_url(user_id)
            if not sheet_url:
                return None
            
            # Extract sheet ID
            sheet_id = self._extract_sheet_id(sheet_url)
            if not sheet_id:
                return None
            
            # Tạo service với sheet ID của user
            user_service = GoogleSheetsService()
            user_service.sheet_id = sheet_id
            user_service.sheet_url = sheet_url
            
            # Override spreadsheet
            user_service.spreadsheet = user_service.client.open_by_key(sheet_id)
            
            # Service đã có method tự động tạo worksheet, không cần gọi thêm
            # user_service sẽ tự động tạo worksheet khi cần
            
            return user_service
            
        except Exception as e:
            logger.error(f"❌ Lỗi tạo user service cho {user_id}: {e}")
            return None
    
    def _get_user_name_from_id(self, user_id: str) -> str:
        """Helper để lấy user name từ ID (fallback)"""
        # Có thể mở rộng sau để lưu thêm user name
        return f"User_{user_id[:8]}"
    
    def get_stats(self) -> Dict:
        """Lấy thống kê user sheets"""
        return {
            'total_users': len(self.user_sheets),
            'users': list(self.user_sheets.keys())
        }
    
    def is_google_sheet_url(self, text: str) -> bool:
        """Kiểm tra text có phải là Google Sheets URL không"""
        google_sheet_patterns = [
            r'docs\.google\.com/spreadsheets',
            r'drive\.google\.com.*spreadsheets',
            r'^[a-zA-Z0-9-_]{44}$'  # Direct sheet ID
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in google_sheet_patterns)
    
    def generate_setup_message(self, user_name: str) -> str:
        """Tạo tin nhắn hướng dẫn setup sheet cho user"""
        return f"""
👋 **Chào mừng {user_name} đến với Bot Quản Lý Thu Chi AI!**

🔧 **THIẾT LẬP LẦN ĐẦU (2 phút):**

📊 **Bạn cần Google Sheet riêng để bảo mật dữ liệu:**

**BƯỚC 1: Tạo Google Sheet**
• Truy cập: https://sheets.google.com
• Tạo sheet mới (hoặc dùng sheet có sẵn)

**BƯỚC 2: Chia sẻ với Bot** ⚠️ **QUAN TRỌNG**
• Click nút "Chia sẻ" ở góc phải màn hình
• Thêm email service account của bot:
📧 `{os.getenv('GOOGLE_SERVICE_EMAIL', 'service-account-email')}`
• **PHẢI** chọn quyền **"Trình chỉnh sửa"** (Editor)
• Click "Gửi" để lưu quyền

**BƯỚC 3: Gửi Link cho Bot**
Gửi link Google Sheet cho bot (copy từ thanh địa chỉ):
`https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit`

✨ **SAU KHI SETUP:**
🤖 Bot tự tạo worksheet `{user_name}` cho bạn
🔒 Chỉ bạn và bot xem được dữ liệu
🚀 Bắt đầu sử dụng: `"500k trà sữa"`, `"5m lương"`

📱 **VÍ DỤ SỬ DỤNG:**
• `"bún 50k, laptop 1.5m"` → Tự tách 2 giao dịch
• `"hôm qua 200k xăng"` → Ghi ngày cụ thể
• `"thống kê ăn uống"` → Xem báo cáo

💡 **Chỉ cần setup 1 lần duy nhất!**
""" 