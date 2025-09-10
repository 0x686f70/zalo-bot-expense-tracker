import logging
from typing import Dict, Any
from utils.date_utils import DateUtils

logger = logging.getLogger(__name__)

def format_currency(amount: float) -> str:
    """
    Format số tiền theo định dạng VNĐ
    
    Args:
        amount: Số tiền
        
    Returns:
        str: Số tiền đã format (VD: 1,500,000 VNĐ)
    """
    try:
        return f"{amount:,.0f} VNĐ"
    except Exception as e:
        logger.error(f"Lỗi format currency: {e}")
        return f"{amount} VNĐ"

def format_statistics(stats: Dict[str, Any], stats_type: str, value: str) -> str:
    """
    Format thống kê thành tin nhắn gửi cho user
    
    Args:
        stats: Dữ liệu thống kê
        stats_type: Loại thống kê
        value: Giá trị thống kê
        
    Returns:
        str: Tin nhắn đã format
    """
    try:
        # Header
        period_desc = DateUtils.format_date_range(stats_type, value)
        response = f"📊 THỐNG KÊ THU CHI {period_desc.upper()}\n\n"
        
        # Tổng quan
        total_income = stats.get('total_income', 0)
        total_expense = stats.get('total_expense', 0)
        balance = stats.get('balance', 0)
        transaction_count = stats.get('transaction_count', 0)
        
        response += f"💰 Tổng thu: {format_currency(total_income)}\n"
        response += f"💸 Tổng chi: {format_currency(total_expense)}\n"
        
        # Hiển thị số dư với biểu tượng tương ứng
        balance_icon = "💵" if balance >= 0 else "⚠️"
        response += f"{balance_icon} Số dư: {format_currency(balance)}\n"
        response += f"📝 Số giao dịch: {transaction_count}\n\n"
        
        # Chi tiết theo danh mục
        income_categories = stats.get('income_categories', {})
        expense_categories = stats.get('expense_categories', {})
        
        if income_categories or expense_categories:
            response += "📈 CHI TIẾT THEO DANH MỤC:\n\n"
        
        # Thu nhập theo danh mục
        if income_categories:
            response += "💰 **Thu nhập theo danh mục:**\n"
            # Sắp xếp theo số tiền giảm dần
            sorted_income = sorted(income_categories.items(), key=lambda x: x[1], reverse=True)
            for i, (category, amount) in enumerate(sorted_income, 1):
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                response += f"  {i}. {category}: {format_currency(amount)} ({percentage:.1f}%)\n"
            response += "\n"
        
        # Chi tiêu theo danh mục
        if expense_categories:
            response += "💸 **Chi tiêu theo danh mục:**\n"
            # Sắp xếp theo số tiền giảm dần
            sorted_expense = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
            for i, (category, amount) in enumerate(sorted_expense, 1):
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                response += f"  {i}. {category}: {format_currency(amount)} ({percentage:.1f}%)\n"
            
            # Thêm top 3 danh mục chi tiêu nhiều nhất
            if len(sorted_expense) > 1:
                response += f"\n🔥 **Top chi tiêu:**\n"
                for i, (category, amount) in enumerate(sorted_expense[:3], 1):
                    if i == 1:
                        response += f"  🥇 {category}: {format_currency(amount)}\n"
                    elif i == 2:
                        response += f"  🥈 {category}: {format_currency(amount)}\n"
                    elif i == 3:
                        response += f"  🥉 {category}: {format_currency(amount)}\n"
        
        # Nếu không có giao dịch
        if transaction_count == 0:
            response = f"📊 THỐNG KÊ THU CHI {period_desc.upper()}\n\n"
            response += "📭 Không có giao dịch nào trong khoảng thời gian này.\n\n"
            response += "💡 Hãy thêm giao dịch đầu tiên bằng lệnh /thu hoặc /chi"
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Lỗi format thống kê: {e}")
        return f"❌ Có lỗi khi hiển thị thống kê {DateUtils.format_date_range(stats_type, value)}"

def format_category_list(categories: Dict[str, list]) -> str:
    """
    Format danh sách danh mục
    
    Args:
        categories: Dict chứa danh mục thu và chi
        
    Returns:
        str: Danh sách đã format
    """
    try:
        response = "📂 DANH MỤC HIỆN CÓ:\n\n"
        
        income_categories = categories.get('Thu', [])
        expense_categories = categories.get('Chi', [])
        
        if income_categories:
            response += "💰 DANH MỤC THU:\n"
            for i, category in enumerate(income_categories, 1):
                response += f"  {i}. {category}\n"
            response += "\n"
        
        if expense_categories:
            response += "💸 DANH MỤC CHI:\n"
            for i, category in enumerate(expense_categories, 1):
                response += f"  {i}. {category}\n"
        
        if not income_categories and not expense_categories:
            response = "📂 Chưa có danh mục nào!\n\n"
            response += "💡 Hãy thêm giao dịch đầu tiên để tạo danh mục."
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Lỗi format danh mục: {e}")
        return "❌ Có lỗi khi hiển thị danh mục"