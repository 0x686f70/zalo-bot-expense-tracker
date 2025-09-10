from datetime import datetime, timedelta
import calendar
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DateUtils:
    """Utility class để xử lý ngày tháng"""
    
    @staticmethod
    def get_date_range(stats_type: str, value: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Tính toán khoảng thời gian dựa trên loại thống kê
        
        Args:
            stats_type: 'ngay', 'tuan', 'thang', 'nam'
            value: Giá trị tương ứng
            
        Returns:
            Tuple[start_date, end_date]
        """
        try:
            current_year = datetime.now().year
            
            if stats_type == 'ngay':
                # Parse ngày: dd/mm/yyyy
                target_date = datetime.strptime(value, "%d/%m/%Y")
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                return start_date, end_date
                
            elif stats_type == 'tuan':
                # Parse tuần: số tuần trong năm hiện tại
                week_num = int(value)
                year = current_year
                
                # Tìm ngày đầu tuần
                jan1 = datetime(year, 1, 1)
                # Tìm thứ 2 đầu tiên của năm
                days_to_monday = (7 - jan1.weekday()) % 7
                if jan1.weekday() == 0:  # Nếu 1/1 là thứ 2
                    days_to_monday = 0
                first_monday = jan1 + timedelta(days=days_to_monday)
                
                # Tính ngày bắt đầu tuần
                start_date = first_monday + timedelta(weeks=week_num-1)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                return start_date, end_date
                
            elif stats_type == 'thang':
                # Parse tháng: mm (năm hiện tại)
                month = int(value)
                year = current_year
                
                # Ngày đầu tháng
                start_date = datetime(year, month, 1)
                
                # Ngày cuối tháng
                last_day = calendar.monthrange(year, month)[1]
                end_date = datetime(year, month, last_day, 23, 59, 59, 999999)
                
                return start_date, end_date
                
            elif stats_type == 'nam':
                # Parse năm: yyyy
                year = int(value)
                
                start_date = datetime(year, 1, 1)
                end_date = datetime(year, 12, 31, 23, 59, 59, 999999)
                
                return start_date, end_date
            
            return None, None
            
        except Exception as e:
            logger.error(f"Lỗi tính toán khoảng thời gian: {e}")
            return None, None
    
    @staticmethod
    def format_date_range(stats_type: str, value: str) -> str:
        """
        Format hiển thị khoảng thời gian
        
        Args:
            stats_type: Loại thống kê
            value: Giá trị
            
        Returns:
            str: Chuỗi mô tả khoảng thời gian
        """
        try:
            if stats_type == 'ngay':
                return f"ngày {value}"
            elif stats_type == 'tuan':
                return f"tuần {value} năm {datetime.now().year}"
            elif stats_type == 'thang':
                return f"tháng {value}/{datetime.now().year}"
            elif stats_type == 'nam':
                return f"năm {value}"
            
            return "khoảng thời gian không xác định"
            
        except Exception as e:
            logger.error(f"Lỗi format khoảng thời gian: {e}")
            return "khoảng thời gian không xác định"

def parse_custom_date(custom_date_str: str = None) -> datetime:
    """
    Parse custom date string thành datetime object
    
    Args:
        custom_date_str: String ngày tùy chỉnh từ AI (VD: "5/9", "hôm qua", "thứ hai", null)
        
    Returns:
        datetime: Ngày được parse hoặc ngày hiện tại nếu None
    """
    from datetime import datetime, timedelta
    import calendar
    
    if not custom_date_str:
        return datetime.now()
    
    custom_date_str = custom_date_str.lower().strip()
    
    try:
        # Xử lý ngày dạng DD/MM
        if '/' in custom_date_str:
            parts = custom_date_str.split('/')
            if len(parts) == 2:
                day = int(parts[0])
                month = int(parts[1])
                year = datetime.now().year
                
                # Tạo datetime object
                target_date = datetime(year, month, day)
                
                # Nếu ngày trong tương lai (của năm hiện tại), có thể là năm trước
                if target_date > datetime.now():
                    target_date = datetime(year - 1, month, day)
                
                return target_date
        
        # Xử lý các từ khóa thời gian
        now = datetime.now()
        
        if custom_date_str in ['hôm nay', 'ngày hôm nay']:
            return now
        elif custom_date_str in ['hôm qua', 'ngày hôm qua']:
            return now - timedelta(days=1)
        elif custom_date_str in ['hôm kia', 'ngày hôm kia']:
            return now - timedelta(days=2)
        elif custom_date_str in ['tuần trước', 'tuần trước']:
            return now - timedelta(days=7)
        elif custom_date_str in ['tháng trước']:
            # Tháng trước cùng ngày
            if now.month == 1:
                return datetime(now.year - 1, 12, min(now.day, 31))
            else:
                prev_month = now.month - 1
                # Lấy số ngày tối đa của tháng trước
                max_day = calendar.monthrange(now.year, prev_month)[1]
                return datetime(now.year, prev_month, min(now.day, max_day))
        
        # Xử lý thứ trong tuần
        weekdays = {
            'thứ hai': 0, 'thứ 2': 0,
            'thứ ba': 1, 'thứ 3': 1,
            'thứ tư': 2, 'thứ 4': 2,
            'thứ năm': 3, 'thứ 5': 3,
            'thứ sáu': 4, 'thứ 6': 4,
            'thứ bảy': 5, 'thứ 7': 5,
            'chủ nhật': 6
        }
        
        if custom_date_str in weekdays:
            target_weekday = weekdays[custom_date_str]
            current_weekday = now.weekday()
            
            # Tính số ngày cần lùi về thứ đó trong tuần trước
            days_back = (current_weekday - target_weekday) % 7
            if days_back == 0:  # Nếu cùng thứ thì lấy tuần trước
                days_back = 7
                
            return now - timedelta(days=days_back)
        
        # Nếu không parse được, trả về hiện tại
        logger.warning(f"Không thể parse custom_date: {custom_date_str}")
        return now
        
    except Exception as e:
        logger.error(f"Lỗi parse custom_date '{custom_date_str}': {e}")
        return datetime.now()
