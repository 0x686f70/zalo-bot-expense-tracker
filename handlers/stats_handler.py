from zalo_bot import Update
from zalo_bot.constants import ChatAction

from utils.format_utils import format_currency, format_statistics
from utils.date_utils import DateUtils
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def _get_current_month_range():
    """Helper để lấy khoảng thời gian tháng hiện tại"""
    now = datetime.now()
    date_utils = DateUtils()
    return date_utils.get_date_range('thang', str(now.month))

async def handle_stats(update: Update, context, sheets_service):
    """Xử lý lệnh thống kê"""
    try:
        # Hiển thị "đang soạn tin..." 
        await context.bot.send_chat_action(
            chat_id=update.message.chat.id,
            action=ChatAction.TYPING
        )
        
        message_text = update.message.text
        
        # Hướng dẫn chuyển sang natural language
        await update.message.reply_text(
            "🤖 **Lệnh /thongke đã được thay thế bằng AI!**\n\n"
            "✨ **Cách mới (đơn giản hơn):**\n"
            "• `\"thống kê\"` → Tháng hiện tại\n"
            "• `\"thống kê hôm nay\"` → Chỉ hôm nay\n"
            "• `\"thống kê hôm qua\"` → Chỉ hôm qua\n"
            "• `\"thống kê tháng 8\"` → Tháng cụ thể\n"
            "• `\"thống kê từ 1/8 đến 15/8\"` → Khoảng tùy chỉnh\n\n"
            "📈 **Thống kê danh mục:**\n"
            "• `\"ăn uống\"` → Chi tiêu ăn uống\n"
            "• `\"ăn uống hôm qua\"` → Danh mục ngày cụ thể\n"
            "• `\"top chi tiêu\"` → Top 5 khoản chi lớn nhất\n\n"
            "🎯 **Ưu điểm:**\n"
            "• Nói chuyện tự nhiên\n"
            "• Thống kê chi tiết với biểu đồ\n"
            "• Hỗ trợ nhiều khoảng thời gian\n\n"
            "💡 **Thử ngay:** Nhắn `\"thống kê\"` thay vì `/thongke`"
        )
        return True
        
    except Exception as e:
        logger.error(f"Lỗi xử lý thống kê: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi tính thống kê. Vui lòng thử lại sau!"
        )
        return False

async def handle_categories(update: Update, context, sheets_service):
    """Xử lý lệnh xem danh mục"""
    try:
        # Hiển thị "đang soạn tin..." nếu có context
        if context and hasattr(context, 'bot'):
            await context.bot.send_chat_action(
                chat_id=update.message.chat.id,
                action=ChatAction.TYPING
            )
        
        user_name = update.message.from_user.display_name or "Người dùng"
        categories = sheets_service.get_categories()
        
        if not categories['Thu'] and not categories['Chi']:
            await update.message.reply_text(
                "📂 Chưa có danh mục nào!\n\n"
                "Hãy thêm giao dịch đầu tiên để tạo danh mục."
            )
            return
        
        response = "📂 DANH MỤC HIỆN CÓ:\n\n"
        
        if categories['Thu']:
            response += "💰 **DANH MỤC THU:**\n"
            for i, category in enumerate(categories['Thu'], 1):
                response += f"  {i}. {category}\n"
            response += "\n"
        
        if categories['Chi']:
            response += "💸 **DANH MỤC CHI:**\n"
            for i, category in enumerate(categories['Chi'], 1):
                response += f"  {i}. {category}\n"
        
        # Thêm thống kê nhanh về danh mục
        total_categories = len(categories.get('Thu', [])) + len(categories.get('Chi', []))
        response += f"\n📊 **Tổng quan:**\n"
        response += f"• Tổng danh mục: {total_categories}\n"
        response += f"• Danh mục thu: {len(categories.get('Thu', []))}\n"
        response += f"• Danh mục chi: {len(categories.get('Chi', []))}\n"
        
        response += f"\n💡 **Gợi ý:** Dùng lệnh thống kê để xem chi tiết theo danh mục:\n"
        response += f"• \"thống kê tháng này\"\n"
        response += f"• \"thống kê tuần này\"\n"
        
        response += f"\n🔗 Xem chi tiết: {sheets_service.get_sheet_url() if sheets_service else 'Google Sheet'}"
        
        await update.message.reply_text(response)
        return True
        
    except Exception as e:
        logger.error(f"Lỗi lấy danh mục: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi lấy danh mục. Vui lòng thử lại sau!"
        )
        return False

async def handle_category_stats(update: Update, context, sheets_service):
    """Xử lý lệnh thống kê theo danh mục chi tiết"""
    try:
        # Hiển thị "đang soạn tin..." nếu có context
        if context and hasattr(context, 'bot'):
            await context.bot.send_chat_action(
                chat_id=update.message.chat.id,
                action=ChatAction.TYPING
            )
        
        user_name = update.message.from_user.display_name or "Người dùng"
        
        # Lấy thống kê tháng này
        start_date, end_date = _get_current_month_range()
        
        if not start_date or not end_date:
            await update.message.reply_text("❌ Không thể xác định khoảng thời gian!")
            return
        
        # Lấy thống kê
        stats = sheets_service.get_statistics(user_name, start_date, end_date)
        
        if stats['transaction_count'] == 0:
            await update.message.reply_text(
                "📊 **THỐNG KÊ THEO DANH MỤC**\n\n"
                "📭 Không có giao dịch nào trong tháng này.\n\n"
                "💡 Hãy thêm giao dịch đầu tiên!"
            )
            return
        
        response = "📊 **THỐNG KÊ THEO DANH MỤC - THÁNG NÀY**\n\n"
        
        # Tổng quan
        response += f"💰 Tổng thu: {format_currency(stats['total_income'])}\n"
        response += f"💸 Tổng chi: {format_currency(stats['total_expense'])}\n"
        balance_icon = "💵" if stats['balance'] >= 0 else "⚠️"
        response += f"{balance_icon} Số dư: {format_currency(stats['balance'])}\n"
        response += f"📝 Số giao dịch: {stats['transaction_count']}\n\n"
        
        # Phân tích chi tiêu theo danh mục
        expense_categories = stats.get('expense_categories', {})
        if expense_categories:
            response += "💸 **PHÂN TÍCH CHI TIÊU:**\n"
            sorted_expense = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
            
            for i, (category, amount) in enumerate(sorted_expense, 1):
                percentage = (amount / stats['total_expense'] * 100) if stats['total_expense'] > 0 else 0
                bar = "█" * min(int(percentage / 5), 10)  # Progress bar
                response += f"  {i}. {category}\n"
                response += f"     💰 {format_currency(amount)} ({percentage:.1f}%)\n"
                response += f"     📊 {bar}\n\n"
        
        # Phân tích thu nhập theo danh mục  
        income_categories = stats.get('income_categories', {})
        if income_categories:
            response += "💰 **PHÂN TÍCH THU NHẬP:**\n"
            sorted_income = sorted(income_categories.items(), key=lambda x: x[1], reverse=True)
            
            for i, (category, amount) in enumerate(sorted_income, 1):
                percentage = (amount / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
                bar = "█" * min(int(percentage / 5), 10)  # Progress bar
                response += f"  {i}. {category}\n"
                response += f"     💰 {format_currency(amount)} ({percentage:.1f}%)\n"
                response += f"     📊 {bar}\n\n"
        
        # Insights
        if expense_categories:
            top_expense = max(expense_categories.items(), key=lambda x: x[1])
            response += f"🎯 **Nhận xét:**\n"
            response += f"• Danh mục chi nhiều nhất: {top_expense[0]}\n"
            response += f"• Chiếm {(top_expense[1]/stats['total_expense']*100):.1f}% tổng chi tiêu\n"
        
        response += f"\n🔗 Xem chi tiết: {sheets_service.get_sheet_url() if sheets_service else 'Google Sheet'}"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Lỗi thống kê danh mục: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi tính thống kê danh mục. Vui lòng thử lại sau!"
        )

async def handle_specific_category_stats(update: Update, context, sheets_service, category_name: str):
    """Xử lý thống kê cho danh mục cụ thể"""
    try:
        # Hiển thị "đang soạn tin..." nếu có context
        if context and hasattr(context, 'bot'):
            await context.bot.send_chat_action(
                chat_id=update.message.chat.id,
                action=ChatAction.TYPING
            )
        
        user_name = update.message.from_user.display_name or "Người dùng"
        
        # Lấy thống kê tháng này
        start_date, end_date = _get_current_month_range()
        
        if not start_date or not end_date:
            await update.message.reply_text("❌ Không thể xác định khoảng thời gian!")
            return
        
        # Lấy thống kê
        stats = sheets_service.get_statistics(user_name, start_date, end_date)
        
        if stats['transaction_count'] == 0:
            await update.message.reply_text(
                f"📊 **THỐNG KÊ {category_name.upper()}**\n\n"
                "📭 Không có giao dịch nào trong tháng này.\n\n"
                "💡 Hãy thêm giao dịch đầu tiên!"
            )
            return
        
        # Xử lý thống kê theo danh mục cụ thể
        if category_name.lower() == "top chi tiêu":
            await _handle_top_expenses(update, stats)
        elif category_name.lower() in ["ăn uống", "xăng xe", "mua sắm", "giải trí", "y tế", "học tập"]:
            await _handle_single_category_stats(update, stats, category_name, sheets_service)
        else:
            # Fallback - hiển thị tất cả danh mục
            await handle_category_stats(update, context, sheets_service)
            
    except Exception as e:
        logger.error(f"Lỗi thống kê danh mục cụ thể: {e}")
        await update.message.reply_text(
            f"❌ Có lỗi xảy ra khi tính thống kê {category_name}. Vui lòng thử lại sau!"
        )

async def _handle_top_expenses(update: Update, stats: dict):
    """Xử lý hiển thị top chi tiêu"""
    expense_categories = stats.get('expense_categories', {})
    
    if not expense_categories:
        await update.message.reply_text(
            "📊 **TOP CHI TIÊU**\n\n"
            "📭 Chưa có chi tiêu nào trong tháng này!"
        )
        return
    
    # Sắp xếp theo số tiền giảm dần
    sorted_expenses = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_expenses[:5]
    
    response = "🔥 **TOP CHI TIÊU THÁNG NÀY**\n\n"
    response += f"💸 Tổng chi tiêu: {format_currency(stats['total_expense'])}\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, (category, amount) in enumerate(top_5):
        percentage = (amount / stats['total_expense'] * 100) if stats['total_expense'] > 0 else 0
        medal = medals[i] if i < len(medals) else f"{i+1}️⃣"
        
        response += f"{medal} **{category}**\n"
        response += f"   💰 {format_currency(amount)} ({percentage:.1f}%)\n"
        
        # Progress bar
        bar_length = min(int(percentage / 5), 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)
        response += f"   📊 {bar}\n\n"
    
    if len(sorted_expenses) > 5:
        response += f"💡 Còn {len(sorted_expenses) - 5} danh mục khác"
    
    await update.message.reply_text(response)

async def _handle_single_category_stats(update: Update, stats: dict, category_name: str, sheets_service):
    """Xử lý thống kê cho một danh mục cụ thể"""
    expense_categories = stats.get('expense_categories', {})
    income_categories = stats.get('income_categories', {})
    
    # Tìm danh mục (case-insensitive)
    found_expense = None
    found_income = None
    
    for cat, amount in expense_categories.items():
        if category_name.lower() in cat.lower() or cat.lower() in category_name.lower():
            found_expense = (cat, amount)
            break
    
    for cat, amount in income_categories.items():
        if category_name.lower() in cat.lower() or cat.lower() in category_name.lower():
            found_income = (cat, amount)
            break
    
    if not found_expense and not found_income:
        await update.message.reply_text(
            f"📊 **THỐNG KÊ {category_name.upper()}**\n\n"
            f"❌ Không tìm thấy danh mục '{category_name}' trong tháng này.\n\n"
            f"💡 Dùng lệnh 'danh mục' để xem tất cả danh mục hiện có."
        )
        return
    
    response = f"📊 **THỐNG KÊ {category_name.upper()} - THÁNG NÀY**\n\n"
    
    if found_expense:
        cat_name, amount = found_expense
        percentage = (amount / stats['total_expense'] * 100) if stats['total_expense'] > 0 else 0
        
        response += f"💸 **Chi tiêu {cat_name}:**\n"
        response += f"   💰 {format_currency(amount)}\n"
        response += f"   📊 {percentage:.1f}% tổng chi tiêu\n"
        
        # So sánh với các danh mục khác
        rank = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
        position = next((i+1 for i, (cat, _) in enumerate(rank) if cat == cat_name), 0)
        response += f"   🏆 Xếp hạng: #{position}/{len(expense_categories)}\n\n"
        
        # Gợi ý
        if percentage > 30:
            response += "⚠️ **Nhận xét:** Danh mục này chiếm tỷ trọng cao!\n"
        elif percentage < 5:
            response += "✅ **Nhận xét:** Chi tiêu hợp lý cho danh mục này.\n"
        else:
            response += "📈 **Nhận xét:** Mức chi tiêu bình thường.\n"
    
    if found_income:
        cat_name, amount = found_income
        percentage = (amount / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
        
        response += f"💰 **Thu nhập {cat_name}:**\n"
        response += f"   💰 {format_currency(amount)}\n"
        response += f"   📊 {percentage:.1f}% tổng thu nhập\n\n"
    
    response += f"\n🔗 Xem chi tiết: {sheets_service.get_sheet_url() if sheets_service else 'Google Sheet'}"
    
    await update.message.reply_text(response)

# Direct versions không cần context (cho natural language handler)
async def handle_specific_category_stats_direct(update: Update, sheets_service, category_name: str, time_period: str = "thang", specific_value: str = None):
    """Xử lý thống kê cho danh mục cụ thể (không cần context) với thời gian từ AI"""
    # TODO: Sử dụng time_period và specific_value từ AI để tính khoảng thời gian
    await handle_specific_category_stats(update, None, sheets_service, category_name)

async def handle_category_stats_direct(update: Update, sheets_service, time_period: str = "thang", specific_value: str = None):
    """Xử lý thống kê tất cả danh mục (không cần context) với thời gian từ AI"""
    # TODO: Sử dụng time_period và specific_value từ AI để tính khoảng thời gian
    await handle_category_stats(update, None, sheets_service)

async def handle_categories_direct(update: Update, sheets_service):
    """Xử lý xem danh mục (không cần context)"""
    await handle_categories(update, None, sheets_service)