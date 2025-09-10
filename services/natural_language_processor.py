import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from services.gemini_ai import GeminiAIService
from performance_optimizer import cache_ai_response, performance_optimizer

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NaturalLanguageProcessor:
    """Xử lý ngôn ngữ tự nhiên để hiểu ý định người dùng"""
    
    def __init__(self):
        self.ai_service = GeminiAIService()
        
    @cache_ai_response(ttl=300)
    def process_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Phân tích tin nhắn tự nhiên và trả về intent + data
        CHỈ XỬ LÝ CÁC TIN NHẮN LIÊN QUAN ĐẾN TÀI CHÍNH
        
        Args:
            message: Tin nhắn từ người dùng
            
        Returns:
            Dict với intent, action, và data hoặc None nếu không liên quan tài chính
        """
        # Try fast processing first for simple messages
        quick_result = self._quick_classify(message)
        if quick_result:
            logger.info(f"⚡ Quick classified: {message[:20]}... -> {quick_result['intent']}")
            return quick_result
        
        if not self.ai_service.is_enabled():
            return self._fallback_process(message)
        
        try:
            prompt = f"""
Phân tích tin nhắn sau và xác định có liên quan đến quản lý tài chính không:

Tin nhắn: "{message}"

CHỈ XỬ LÝ các ý định liên quan đến tài chính:
1. EXPENSE (Chi tiêu): 
   - Một món: "500k trà sữa", "mua áo 300k", "200k xăng"
   - Nhiều món cùng danh mục: "bún 80k và phở 150k" → CỘNG TỔNG: 80000 + 150000 = 230000
   - QUAN TRỌNG - Nhiều món KHÁC danh mục: "bún 12k, gà 20k, laptop 1.5m, 200k xăng" → TỰ ĐỘNG TÁCH THÀNH NHIỀU GIAO DỊCH
   - QUAN TRỌNG - Khác danh mục với từ kết nối: "480k nướng, 575k siêu thị" → TÁCH THÀNH 2 GIAO DỊCH RIÊNG
   - QUAN TRỌNG - KÈM NGÀY CỤ THỂ: "5/9 bánh 200k", "hôm qua 80k đi chợ", "tuần trước mua áo 300k"
2. INCOME (Thu nhập): "thu 5m lương", "5m lương", "nhận 1tr", "được 500k"
   - QUAN TRỌNG - KÈM NGÀY CỤ THỂ: "2/9 thưởng 500k", "hôm qua nhận 1tr", "thứ hai lương 5m"
3. STATS (Thống kê tổng): 
   - Mặc định: "thống kê", "báo cáo", "tổng kết" → THÁNG HIỆN TẠI
   - Cụ thể: "thống kê tháng trước", "báo cáo tháng 8", "thống kê tuần này", "thống kê hôm nay"
4. CATEGORY_STATS (Thống kê danh mục cụ thể):
   - Mặc định: "thống kê ăn uống", "top chi tiêu", "ăn uống" → THÁNG HIỆN TẠI  
   - Cụ thể: "ăn uống tháng 8", "top chi tiêu tuần này", "thống kê xăng xe tháng trước"
   - QUAN TRỌNG: "ăn uống hôm nay", "xăng xe hôm nay", "mua sắm ngày hôm nay" → NGÀY HIỆN TẠI

HƯỚNG DẪN XỬ LÝ THỜI GIAN CHO AI - PHÂN TÍCH KỸ LƯỠNG:
*** CHÚ Ý QUAN TRỌNG: PHẢI PHÂN TÍCH CHÍNH XÁC TỪ THỜI GIAN TRONG TIN NHẮN ***

- "hôm nay", "ngày hôm nay", "[danh_mục] hôm nay", "ngày này" → time_period: "ngay"
- "thống kê hôm qua", "báo cáo hôm qua", "thống kê ngày hôm qua" → time_period: "ngay", specific_value: "hôm qua"
- "thống kê hôm kia", "báo cáo hôm kia", "thống kê ngày hôm kia" → time_period: "ngay", specific_value: "hôm kia"
- "thống kê 2/9", "báo cáo 15/8", "thống kê ngày 02/09" → time_period: "ngay", specific_value: "2/9", "15/8", "02/09"
- "tuần này", "tuần hiện tại", "[danh_mục] tuần này" → time_period: "tuan"  
- "tháng này", "tháng hiện tại", "[danh_mục]" (CHÍNH XÁC KHÔNG có từ thời gian nào khác) → time_period: "thang"
- "năm này", "năm hiện tại", "[danh_mục] năm này" → time_period: "nam"
- "tháng trước", "[danh_mục] tháng trước" → time_period: "thang", specific_value: "thang_truoc"
- "tháng 8", "tháng 12", "[danh_mục] tháng 8" → time_period: "thang", specific_value: "8" hoặc "12"
- "tuần trước", "[danh_mục] tuần trước" → time_period: "tuan", specific_value: "tuan_truoc"

*** CẨN THẬN: "ăn uống hôm nay" KHÁC VỚI "ăn uống" - PHẢI NHẬN DIỆN "hôm nay" ***

HƯỚNG DẪN XỬ LÝ NGÀY THÁNG CHO CHI TIÊU/THU NHẬP:
*** QUAN TRỌNG: PHẢI PHÂN TÍCH NGÀY THÁNG TRONG TIN NHẮN EXPENSE/INCOME ***

NHẬN DIỆN NGÀY CỤ THỂ:
- "5/9 bánh 200k", "2/9 thưởng 500k" → custom_date: "5/9", "2/9"
- "15/8 mua áo 300k", "10/12 nhận lương" → custom_date: "15/8", "10/12"
- "hôm qua 80k đi chợ", "hôm kia nhận 1tr" → custom_date: "hôm qua", "hôm kia"
- "thứ hai mua sách 50k", "thứ ba lương 5m" → custom_date: "thứ hai", "thứ ba"
- "tuần trước mua laptop", "tháng trước thưởng" → custom_date: "tuần trước", "tháng trước"
- "500k trà sữa" (không có ngày) → custom_date: null

CHÚ Ý: Nếu KHÔNG có ngày cụ thể → custom_date: null (ghi vào ngày hiện tại)

QUAN TRỌNG - KHOẢNG THỜI GIAN CỤ THỂ:
- "từ 01/08 đến 31/08", "từ 1/8 đến 31/8" → time_period: "custom", specific_value: "01/08-31/08"
- "từ 01/09 đến 05/09", "từ 1/9 đến 5/9" → time_period: "custom", specific_value: "01/09-05/09"
- "từ 15/12 đến 20/12" → time_period: "custom", specific_value: "15/12-20/12"
- Bất kỳ "từ XX/XX đến YY/YY" → time_period: "custom", specific_value: "XX/XX-YY/YY"

QUY TẮC TÍNH TOÁN SỐ TIỀN:
- k = 1,000 (VD: 80k = 80000)
- m/tr/triệu = 1,000,000 (VD: 1.5m = 1500000)
- Nhiều món: PHẢI CỘNG TẤT CẢ (VD: "80k + 150k" = 230000, KHÔNG PHẢI 230)
- Đơn vị: Luôn chuyển về VND (số nguyên)

QUY TẮC PHÂN LOẠI DANH MỤC CHO EXPENSE - PHÂN TÍCH KỸ LƯỠNG:
*** QUAN TRỌNG: PHẢI PHÂN TÍCH TỪ KHÓA CHÍNH XÁC ***

- Ăn uống: 
  * Món ăn: bún, phở, gà, rau, cơm, bánh, thịt, cá, tôm, nướng, luộc, xào, chiên, lẩu, nồi, canh, súp
  * Thức uống: trà sữa, cà phê, nước, bia, rượu, sinh tố, nước ngọt, soda
  * Địa điểm: nhà hàng, quán ăn, quán cà phê, quán nhậu, buffet, food court, căng tin
  * Nguyên liệu: thịt, rau, củ, quả, gạo, mì, bánh mì, sữa, trứng, gia vị
  * Đồ ăn vặt: bánh kẹo, snack, kẹo, chocolate, bánh quy

- Di chuyển: xăng xe, vé xe buýt, taxi, grab, đi lại, gửi xe, xe ôm, bus, xanhsm, bee, tiền xe, phí đường, cầu phí

- Mua sắm: quần áo, giày dép, đồ dùng, mỹ phẩm, điện tử, áo, giày, máy tính, laptop, điện thoại, túi xách

- Giải trí: xem phim, game, du lịch, karaoke, bar, vui chơi, giải trí, concert, show

- Y tế: thuốc, khám bệnh, nha khoa, bảo hiểm y tế, bác sĩ, bệnh viện, xét nghiệm

- Học tập: sách vở, khóa học, học phí, văn phòng phẩm, sách, học, giáo dục

- Nhà cửa: tiền nhà, điện nước, internet, sửa chữa, nhà, gas, wifi

- Khác: những thứ THỰC SỰ không thuộc 7 danh mục trên

*** LƯU Ý ĐẶC BIỆT - QUAN TRỌNG NHẤT: ***
- "nướng" = NẤU ĂN → Ăn uống (KHÔNG PHẢI Khác!)
- "luộc", "xào", "chiên" = NẤU ĂN → Ăn uống (KHÔNG PHẢI Khác!)
- "thịt", "cá", "gà", "tôm" = THỰC PHẨM → Ăn uống (KHÔNG PHẢI Khác!)
- "rau", "củ", "quả" = THỰC PHẨM → Ăn uống (KHÔNG PHẢI Khác!)
- "đi chợ", "mua đồ ăn" = MUA THỰC PHẨM → Ăn uống (KHÔNG PHẢI Mua sắm!)

*** TUYỆT ĐỐI KHÔNG ĐƯỢC PHÂN LOẠI SAI! ***

*** QUY TẮC QUAN TRỌNG CHO MULTIPLE_EXPENSES: ***
- PHẢI nhận diện chính xác khi có nhiều món KHÁC danh mục
- VD: "480k nướng, 575k siêu thị" = KHÁC danh mục → MULTIPLE_EXPENSES

CÁCH PHÂN TÍCH ĐÚNG:
1. "480k nướng" → Ăn uống
2. "575k siêu thị" → Mua sắm  
3. Ăn uống ≠ Mua sắm → MULTIPLE_EXPENSES

KẾT QUẢ PHẢI TẠO cho "hôm qua 480k nướng, 575k siêu thị":
{{"intent": "MULTIPLE_EXPENSES", "data": {{"transactions": [
  {{"amount": 480000, "description": "nướng", "category": "Ăn uống", "custom_date": "hôm qua"}},
  {{"amount": 575000, "description": "siêu thị", "category": "Mua sắm", "custom_date": "hôm qua"}}
]}}}}

CHÚ Ý: CẢ 2 transactions đều có custom_date: "hôm qua" vì từ thời gian ở ĐẦU tin nhắn

TUYỆT ĐỐI KHÔNG ĐƯỢC:
- Gộp chung: amount=1055000, description="nướng và siêu thị"
- Sai intent: EXPENSE thay vì MULTIPLE_EXPENSES

*** LƯU Ý QUAN TRỌNG VỀ CUSTOM_DATE CHO MULTIPLE_EXPENSES: ***
- Nếu có ngày ở đầu tin nhắn → TẤT CẢ transactions dùng cùng custom_date
- VD: "hôm qua 480k nướng, 575k siêu thị" → custom_date: "hôm qua" cho CẢ 2 transactions
- VD: "5/9 bún 12k, laptop 1.5m" → custom_date: "5/9" cho CẢ 2 transactions
- Nếu KHÔNG có ngày → custom_date: null cho tất cả

*** PHÂN TÍCH CUSTOM_DATE CHO MULTIPLE_EXPENSES: ***
Step 1: Tìm từ thời gian ở ĐẦU tin nhắn ("hôm qua", "5/9", "thứ hai")
Step 2: Nếu có → Áp dụng cho TẤT CẢ transactions trong array
Step 3: Nếu không có → custom_date: null cho tất cả
5. MULTIPLE_EXPENSES (Nhiều khoản chi khác danh mục): 
   - Khi có items thuộc nhiều danh mục khác nhau
   - PHẢI TÁCH RIÊNG từng khoản với amount và category riêng biệt
   - KHÔNG ĐƯỢC gộp chung thành một transaction
6. CATEGORY_LIST (Xem danh mục): "danh mục", "categories", "xem danh mục"
7. HELP (Trợ giúp): "help", "hướng dẫn"

KHÔNG XỬ LÝ:
- Chào hỏi thông thường: "xin chào", "bạn khỏe không"
- Câu hỏi cá nhân: "bạn ăn cơm chưa", "hôm nay thế nào"
- Trò chuyện chung: "thời tiết", "tin tức"

Nếu tin nhắn KHÔNG liên quan đến tài chính, trả về:
{{
    "intent": "HELP_GUIDE",
    "confidence": 1.0,
    "data": {{}}
}}

Nếu liên quan đến tài chính, trả về:
{{
    "intent": "EXPENSE|INCOME|STATS|CATEGORY_STATS|CATEGORY_LIST|MULTIPLE_EXPENSES|HELP",
    "confidence": 0.0-1.0,
    "data": {{
        "amount": số_tiền_hoặc_null (QUAN TRỌNG: Với nhiều món PHẢI CỘNG TỔNG tất cả, VD: 80k+150k=230000, KHÔNG được là 230),
        "description": "mô_tả",
        "category": "danh_mục" (chỉ cho EXPENSE/INCOME, PHẢI phân loại chính xác theo quy tắc trên),
        "custom_date": "ngày_cụ_thể_hoặc_null" (VD: "5/9", "2/9", "hôm qua", "tuần trước", "thứ hai", null nếu không có),
        "transactions": [array của nhiều giao dịch] (chỉ cho MULTIPLE_EXPENSES - mỗi transaction có amount, description, category, custom_date riêng),
        "time_period": "ngay|tuan|thang|nam|custom" (cho STATS & CATEGORY_STATS, mặc định "thang"),
        "specific_value": "số_hoặc_keyword" (VD: "8", "12", "thang_truoc", "tuan_truoc"),
        "category_name": "tên_danh_mục" (chỉ cho CATEGORY_STATS, VD: "ăn uống", "xăng xe", "mua sắm")
    }}
}}

VÍ DỤ CỤ THỂ CHO NHIỀU MÓN:
- "bún 80k và phở 150k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 230000, "description": "bún và phở", "category": "Ăn uống", "custom_date": null}}}}
- "bún 12k, gà 20k, rau 70k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 102000, "description": "bún, gà, rau", "category": "Ăn uống", "custom_date": null}}}}
- "mua áo 300k và giày 200k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 500000, "description": "mua áo và giày", "category": "Mua sắm", "custom_date": null}}}}
- "1.5m laptop và 500k chuột" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 2000000, "description": "laptop và chuột", "category": "Mua sắm", "custom_date": null}}}}
- "hôm qua bún 80k và phở 150k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 230000, "description": "bún và phở", "category": "Ăn uống", "custom_date": "hôm qua"}}}}
- "3/9 mua áo 300k và giày 200k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 500000, "description": "mua áo và giày", "category": "Mua sắm", "custom_date": "3/9"}}}}

VÍ DỤ CHO MỘT MÓN:
- "500k trà sữa" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 500000, "description": "trà sữa", "category": "Ăn uống", "custom_date": null}}}}
- "480k nướng" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 480000, "description": "nướng", "category": "Ăn uống", "custom_date": null}}}}
- "200k xăng xe" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 200000, "description": "xăng xe", "category": "Di chuyển", "custom_date": null}}}}
- "150k thịt" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 150000, "description": "thịt", "category": "Ăn uống", "custom_date": null}}}}
- "80k rau củ" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 80000, "description": "rau củ", "category": "Ăn uống", "custom_date": null}}}}

VÍ DỤ CHO GIAO DỊCH CÓ NGÀY CỤ THỂ:
- "5/9 bánh 200k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 200000, "description": "bánh", "category": "Ăn uống", "custom_date": "5/9"}}}}
- "hôm qua 480k nướng" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 480000, "description": "nướng", "category": "Ăn uống", "custom_date": "hôm qua"}}}}
- "hôm qua 80k đi chợ" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 80000, "description": "đi chợ", "category": "Ăn uống", "custom_date": "hôm qua"}}}}
- "3/9 thịt nướng 350k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 350000, "description": "thịt nướng", "category": "Ăn uống", "custom_date": "3/9"}}}}
- "2/9 thưởng 500k" → {{"intent": "INCOME", "confidence": 0.9, "data": {{"amount": 500000, "description": "thưởng", "category": "Thưởng", "custom_date": "2/9"}}}}
- "thứ hai lương 5m" → {{"intent": "INCOME", "confidence": 0.9, "data": {{"amount": 5000000, "description": "lương", "category": "Lương", "custom_date": "thứ hai"}}}}
- "tuần trước mua áo 300k" → {{"intent": "EXPENSE", "confidence": 0.9, "data": {{"amount": 300000, "description": "mua áo", "category": "Mua sắm", "custom_date": "tuần trước"}}}}

VÍ DỤ CHO NHIỀU KHOẢN CHI KHÁC DANH MỤC:
- "bún 12k, gà 20k, laptop 1.5m, 200k xăng" → {{"intent": "MULTIPLE_EXPENSES", "confidence": 0.9, "data": {{"transactions": [{{"amount": 32000, "description": "bún, gà", "category": "Ăn uống", "custom_date": null}}, {{"amount": 1500000, "description": "laptop", "category": "Mua sắm", "custom_date": null}}, {{"amount": 200000, "description": "xăng", "category": "Di chuyển", "custom_date": null}}]}}}}
- "480k nướng, 575k siêu thị" → {{"intent": "MULTIPLE_EXPENSES", "confidence": 0.9, "data": {{"transactions": [{{"amount": 480000, "description": "nướng", "category": "Ăn uống", "custom_date": null}}, {{"amount": 575000, "description": "siêu thị", "category": "Mua sắm", "custom_date": null}}]}}}}
- "hôm qua 480k nướng, 575k siêu thị" → {{"intent": "MULTIPLE_EXPENSES", "confidence": 0.9, "data": {{"transactions": [{{"amount": 480000, "description": "nướng", "category": "Ăn uống", "custom_date": "hôm qua"}}, {{"amount": 575000, "description": "siêu thị", "category": "Mua sắm", "custom_date": "hôm qua"}}]}}}}
- "thứ hai 100k bánh, 500k laptop" → {{"intent": "MULTIPLE_EXPENSES", "confidence": 0.9, "data": {{"transactions": [{{"amount": 100000, "description": "bánh", "category": "Ăn uống", "custom_date": "thứ hai"}}, {{"amount": 500000, "description": "laptop", "category": "Mua sắm", "custom_date": "thứ hai"}}]}}}}
- "5/9 bún 12k, gà 20k, laptop 1.5m, 200k xăng" → {{"intent": "MULTIPLE_EXPENSES", "confidence": 0.9, "data": {{"transactions": [{{"amount": 32000, "description": "bún, gà", "category": "Ăn uống", "custom_date": "5/9"}}, {{"amount": 1500000, "description": "laptop", "category": "Mua sắm", "custom_date": "5/9"}}, {{"amount": 200000, "description": "xăng", "category": "Di chuyển", "custom_date": "5/9"}}]}}}}

VÍ DỤ CHO THỐNG KÊ:
- "thống kê" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "thang"}}}}
- "thống kê tháng trước" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "thang", "specific_value": "thang_truoc"}}}}
- "báo cáo tháng 8" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "thang", "specific_value": "8"}}}}
- "thống kê tuần này" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "tuan"}}}}
- "thống kê 2/9" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay", "specific_value": "2/9"}}}}
- "báo cáo ngày 15/8" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay", "specific_value": "15/8"}}}}
- "thống kê ngày 02/09" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay", "specific_value": "02/09"}}}}
- "thống kê từ 01/08 đến 31/08" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "custom", "specific_value": "01/08-31/08"}}}}
- "báo cáo từ 1/9 đến 5/9" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "custom", "specific_value": "01/09-05/09"}}}}
- "thống kê hôm nay" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay"}}}}
- "thống kê hôm qua" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay", "specific_value": "hôm qua"}}}}
- "báo cáo hôm kia" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay", "specific_value": "hôm kia"}}}}
- "báo cáo ngày hôm nay" → {{"intent": "STATS", "confidence": 0.9, "data": {{"time_period": "ngay"}}}}

VÍ DỤ CHO THỐNG KÊ DANH MỤC:
- "ăn uống" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "ăn uống", "time_period": "thang"}}}}
- "ăn uống hôm nay" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "ăn uống", "time_period": "ngay"}}}}
- "ăn uống tháng 8" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "ăn uống", "time_period": "thang", "specific_value": "8"}}}}
- "xăng xe tuần này" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "xăng xe", "time_period": "tuan"}}}}
- "mua sắm ngày hôm nay" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "mua sắm", "time_period": "ngay"}}}}
- "top chi tiêu tuần này" → {{"intent": "CATEGORY_STATS", "confidence": 0.9, "data": {{"category_name": "top chi tiêu", "time_period": "tuan"}}}}

Chỉ trả về JSON, không giải thích gì thêm.
"""
            
            response = self.ai_service._generate_content(prompt)
            
            # Parse JSON response (remove markdown formatting if present)
            try:
                # Clean response - remove ```json and ``` if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                result = json.loads(clean_response)
                logger.info(f"AI phân tích: '{message}' -> {result['intent']} ({result.get('confidence', 0):.2f})")
                return result
            except json.JSONDecodeError:
                logger.warning(f"AI trả về JSON không hợp lệ: {response}")
                return self._fallback_process(message)
                
        except Exception as e:
            logger.error(f"Lỗi xử lý ngôn ngữ tự nhiên: {e}")
            return self._fallback_process(message)
    
    def _fallback_process(self, message: str) -> Dict[str, Any]:
        """Fallback đơn giản khi AI không khả dụng - CHỈ PHÁT HIỆN CƠ BẢN"""
        message_lower = message.lower().strip()
        
        # Basic financial keywords detection
        financial_keywords = [
            'chi', 'tiêu', 'mua', 'trả', 'thu', 'nhận', 'lương', 'thưởng',
            'thống kê', 'báo cáo', 'tổng kết', 'danh mục', 'help', 'hướng dẫn'
        ]
        
        # Check if message contains financial content
        has_financial_content = any(keyword in message_lower for keyword in financial_keywords)
        has_numbers = bool(re.search(r'\d+', message_lower))
        
        if has_financial_content or has_numbers:
            # Let the user know AI would handle this better
            return {
                "intent": "HELP_GUIDE",
                "confidence": 0.9,
                    "data": {
                    "message": "AI_UNAVAILABLE",
                    "suggestion": "⚠️ Tính năng AI tạm thời không khả dụng. Vui lòng sử dụng lệnh cụ thể:\n\n• /chi 500k trà sữa\n• /thu 5m lương\n• /thongke thang 12\n• /danhmuc"
                }
            }
        
        # Non-financial content
        return {
            "intent": "HELP_GUIDE",
            "confidence": 1.0,
            "data": {}
        }
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse số tiền từ string"""
        import re
        
        # Remove spaces and normalize
        amount_str = amount_str.lower().strip()
        
        # Extract number and unit
        match = re.match(r'(\d+(?:[.,]\d+)?)\s*([kmtr]|triệu|nghìn)?', amount_str)
        if not match:
            return None
        
        number = float(match.group(1).replace(',', '.'))
        unit = match.group(2) or ''
        
        # Convert based on unit
        if unit in ['k', 'nghìn']:
            return number * 1000
        elif unit in ['m', 'tr', 'triệu']:
            return number * 1000000
        else:
            return number
    
    def _quick_classify(self, message: str) -> Optional[Dict[str, Any]]:
        """Quick classification for simple messages without AI"""
        import re
        
        message_lower = message.lower()
        
        # Skip complex messages
        if any(word in message_lower for word in [',', ' và ', 'hôm qua', 'ngày', '/', 'từ', 'đến']):
            return None
        
        # Check for income keywords first to avoid misclassifying as expense
        income_keywords = ['lương', 'thưởng', 'thu', 'nhận', 'được', 'tiền lương']
        if any(keyword in message_lower for keyword in income_keywords):
            # Skip expense detection if income keywords found
            pass
        else:
            # Quick expense detection (only if no income keywords)
            expense_pattern = r'(\d+(?:\.\d+)?)\s*([kmKM])\s*([\w\s]+)'
            expense_match = re.search(expense_pattern, message)
            if expense_match:
                number = float(expense_match.group(1))
                suffix = expense_match.group(2).lower()
                description = expense_match.group(3).strip()
                
                # Calculate amount
                amount = int(number * 1000) if suffix == 'k' else int(number * 1000000)
                
                # Quick categorization
                category = 'Khác'  # default
                if any(word in message_lower for word in ['bún', 'phở', 'cơm', 'bánh', 'trà sữa', 'cà phê', 'nướng']):
                    category = 'Ăn uống'
                elif any(word in message_lower for word in ['xăng', 'taxi', 'grab']):
                    category = 'Di chuyển'
                elif any(word in message_lower for word in ['áo', 'laptop', 'điện thoại']):
                    category = 'Mua sắm'
                
                return {
                    'intent': 'EXPENSE',
                    'confidence': 0.85,
                    'data': {
                        'amount': amount,
                        'description': description,
                        'category': category
                    }
                }
        
        # Quick income detection - hỗ trợ cả 2 pattern: "thu 5m" và "5m lương"
        income_keywords = ['thu', 'lương', 'nhận', 'được', 'thưởng', 'tiền lương', 'lương tháng']
        
        # Pattern 1: "thu 5m", "nhận 1tr"
        income_pattern1 = r'(thu|nhận|được|thưởng)\s*(\d+(?:\.\d+)?)\s*([kmKM])'
        # Pattern 2: "5m lương", "1tr thưởng"  
        income_pattern2 = r'(\d+(?:\.\d+)?)\s*([kmKM])\s*(lương|thưởng|tiền lương)'
        
        income_match = re.search(income_pattern1, message_lower) or re.search(income_pattern2, message_lower)
        if income_match or any(keyword in message_lower for keyword in income_keywords):
            amount_match = re.search(r'(\d+(?:\.\d+)?)\s*([kmKM])', message)
            if amount_match:
                number = float(amount_match.group(1))
                suffix = amount_match.group(2).lower()
                amount = int(number * 1000) if suffix == 'k' else int(number * 1000000)
                
                # Quick income categorization
                category = 'Khác'  # default
                if any(word in message_lower for word in ['lương', 'tiền lương']):
                    category = 'Lương'
                elif any(word in message_lower for word in ['thưởng', 'bonus']):
                    category = 'Thưởng'
                elif any(word in message_lower for word in ['bán', 'kinh doanh']):
                    category = 'Kinh doanh'
                
                return {
                    'intent': 'INCOME',
                    'confidence': 0.85,
                    'data': {
                        'amount': amount,
                        'description': message,
                        'category': category
                    }
                }
        
        # Quick stats detection
        if any(word in message_lower for word in ['thống kê', 'báo cáo']):
            time_period = 'thang'  # default
            if 'hôm nay' in message_lower:
                time_period = 'ngay'
            elif 'tuần' in message_lower:
                time_period = 'tuan'
            
            return {
                'intent': 'STATS',
                'confidence': 0.8,
                'data': {
                    'time_period': time_period
                }
            }
        
        return None

# Đã xóa generate_response_for_unknown - không cần thiết nữa 