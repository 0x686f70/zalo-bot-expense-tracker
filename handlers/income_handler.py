from zalo_bot import Update
from zalo_bot.constants import ChatAction
from utils.format_utils import format_currency
import logging

logger = logging.getLogger(__name__)

async def handle_income(update: Update, context, sheets_service):
    """Xử lý lệnh thêm khoản thu"""
    try:
        # Hiển thị "đang soạn tin..." 
        await context.bot.send_chat_action(
            chat_id=update.message.chat.id,
            action=ChatAction.TYPING
        )
        
        user_name = update.message.from_user.display_name or "Người dùng"
        message_text = update.message.text
        
        # Hướng dẫn chuyển sang natural language
        await update.message.reply_text(
            "🤖 Lệnh /thu đã được thay thế bằng AI!\n\n"
            "✨ Cách mới (đơn giản hơn):\n"
            "• \"5m lương\" → Tự động ghi thu nhập\n"
            "• \"nhận 1tr thưởng\" → AI hiểu từ khóa\n"
            "• \"2/9 được 500k\" → Thu nhập ngày cụ thể\n\n"
            "🎯 Ưu điểm:\n"
            "• Nói chuyện tự nhiên\n"
            "• AI tự phân loại\n"
            "• Hỗ trợ ngày tùy chỉnh\n\n"
            "💡 Thử ngay: Nhắn \"5m lương\" thay vì /thu 5m lương"
        )
        return True
        
    except Exception as e:
        logger.error(f"Lỗi xử lý khoản thu: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi xử lý. Vui lòng thử lại sau!"
        )
        return False
