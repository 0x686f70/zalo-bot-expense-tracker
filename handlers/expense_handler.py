from zalo_bot import Update
from zalo_bot.constants import ChatAction
from utils.format_utils import format_currency
import logging

logger = logging.getLogger(__name__)

async def handle_expense(update: Update, context, sheets_service):
    """Xử lý lệnh thêm khoản chi"""
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
            "🤖 **Lệnh /chi đã được thay thế bằng AI!**\n\n"
            "✨ **Cách mới (đơn giản hơn):**\n"
            "• `\"500k trà sữa\"` → Tự động phân loại \"Ăn uống\"\n"
            "• `\"hôm qua 200k xăng\"` → Ghi ngày cụ thể\n"
            "• `\"bún 50k, laptop 1.5m\"` → Tự tách 2 giao dịch\n\n"
            "🎯 **Ưu điểm:**\n"
            "• Nói chuyện tự nhiên\n"
            "• AI tự phân loại danh mục\n"
            "• Tự động tách nhiều khoản\n"
            "• Hỗ trợ ngày quá khứ\n\n"
            "💡 **Thử ngay:** Nhắn `\"500k trà sữa\"` thay vì `/chi 500k trà sữa`"
        )
        return True
        
    except Exception as e:
        logger.error(f"Lỗi xử lý khoản chi: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi xử lý. Vui lòng thử lại sau!"
        )
        return False
