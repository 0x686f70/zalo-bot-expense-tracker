import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from zalo_bot import Update
from zalo_bot.constants import ChatAction
from services.natural_language_processor import NaturalLanguageProcessor
from services.google_sheets import GoogleSheetsService
from services.gemini_ai import GeminiAIService
from utils.format_utils import format_currency


logger = logging.getLogger(__name__)

class NaturalLanguageHandler:
    """Handler xử lý tin nhắn ngôn ngữ tự nhiên"""
    
    def __init__(self, sheets_service: GoogleSheetsService = None, user_sheet_manager = None):
        self.nlp = NaturalLanguageProcessor()
        self.sheets_service = sheets_service
        self.user_sheet_manager = user_sheet_manager
        self.ai_service = GeminiAIService()
    
    async def handle_natural_message(self, update: Update, context) -> bool:
        """
        Xử lý tin nhắn tự nhiên
        
        Returns:
            bool: True nếu đã xử lý, False nếu không hiểu
        """
        # Hiển thị "đang soạn tin..." ngay khi nhận tin nhắn
        await context.bot.send_chat_action(
            chat_id=update.message.chat.id,
            action=ChatAction.TYPING
        )
        
        message_text = update.message.text
        user_name = update.message.from_user.display_name or "Người dùng"
        user_id = update.message.from_user.id
        
        # Kiểm tra private mode và user setup
        if self.user_sheet_manager:
            # Private mode - kiểm tra user đã setup sheet chưa
            if not self.user_sheet_manager.has_user_sheet(user_id):
                # Kiểm tra xem message có phải là Google Sheet URL không
                if self.user_sheet_manager.is_google_sheet_url(message_text):
                    await self._handle_sheet_setup(update, context)
                    return True
                else:
                    # Chưa setup sheet, yêu cầu setup
                    await self._handle_setup_request(update, context)
                    return True
        
        # Phân tích ý định
        try:
            intent_result = self.nlp.process_message(message_text)
            
            # Nếu process_message trả về coroutine, await nó
            if hasattr(intent_result, '__await__'):
                intent_result = await intent_result
            
            if not intent_result:
                # Không thể phân tích - bỏ qua
                return True
            
            intent = intent_result['intent']
        except Exception as e:
            logger.error(f"Lỗi phân tích ý định: {e}")
            return True
        
        # Nếu là HELP_GUIDE - tin nhắn không liên quan tài chính, trả lời hướng dẫn
        if intent == 'HELP_GUIDE':
            await self._handle_help_guide(update, context)
            return True
        
        # Nếu confidence thấp, bỏ qua
        if intent_result['confidence'] < 0.5:
            return True
        
        data = intent_result.get('data', {})
        
        try:
            if intent == 'EXPENSE':
                await self._handle_expense(update, data, user_name)
                return True
                
            elif intent == 'INCOME':
                await self._handle_income(update, data, user_name)
                return True
                
            elif intent == 'MULTIPLE_EXPENSES':
                await self._handle_multiple_expenses(update, data, user_name)
                return True
                
            elif intent == 'LENDING':
                await self._handle_lending(update, data, user_name)
                return True
                
            elif intent == 'BORROWING':
                await self._handle_borrowing(update, data, user_name)
                return True
                
            elif intent == 'STATS':
                await self._handle_stats(update, data)
                return True
                
            elif intent == 'CATEGORY_STATS':
                await self._handle_category_stats(update, data)
                return True
                
            elif intent == 'CATEGORY_LIST':
                await self._handle_category_list(update)
                return True
                
            elif intent == 'HELP':
                await self._handle_help(update)
                return True
                
            else:
                # Tin nhắn không được hỗ trợ - bỏ qua
                return True
                
        except Exception as e:
            logger.error(f"Lỗi xử lý natural language: {e}")
            await update.message.reply_text(
                "🚫 Có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại!"
            )
            return True
    
    async def _handle_expense(self, update: Update, data: Dict[str, Any], user_name: str):
        """Xử lý khoản chi"""
        amount = data.get('amount')
        description = data.get('description', 'chi tiêu')
        
        if not amount or amount <= 0:
            await update.message.reply_text(
                "🤔 Tôi không thấy số tiền rõ ràng. Bạn có thể nói cụ thể hơn không?\n\n" +
                "💡 Ví dụ: '500k trà sữa' hoặc '200k đổ xăng'"
            )
            return
        
        # Sử dụng category từ AI hoặc fallback
        category = data.get('category')
        if not category:
            # Fallback nếu AI không trả về category
            if self.ai_service.is_enabled():
                category = self.ai_service.categorize_expense(description)
            else:
                category = "Khác"
        
        # Lưu vào Google Sheets
        custom_date = data.get('custom_date')
        success = self._add_transaction_with_user_info(
            transaction_type="Chi",
            amount=amount,
            category=category,
            note=description,
            user_name=user_name,
            update=update,
            custom_date=custom_date
        )
        
        if success:
            from datetime import datetime
            from utils.date_utils import parse_custom_date
            
            # Hiển thị thời gian thực tế được ghi nhận  
            actual_datetime = parse_custom_date(custom_date)
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            
            if custom_date:
                date_info = f"📅 Ngày: {actual_datetime.strftime('%d/%m/%Y')} (ghi lúc {current_time})"
            else:
                date_info = f"📅 Thời gian: {current_time}"
            
            response = f"""
✅ Đã ghi nhận khoản chi vào {current_time}!

💸 Số tiền: {format_currency(amount)}
📂 Danh mục: {category} {"🤖" if self.ai_service.is_enabled() else ""}
📝 Ghi chú: {description}
{date_info}
👤 Người dùng: {user_name}

🔗 Xem chi tiết: {self._get_sheet_url(update)}
"""
        else:
            response = "🚫 Có lỗi khi lưu dữ liệu. Vui lòng thử lại!"
        
        await update.message.reply_text(response.strip())
    
    async def _handle_income(self, update: Update, data: Dict[str, Any], user_name: str):
        """Xử lý khoản thu"""
        amount = data.get('amount')
        description = data.get('description', 'thu nhập')
        
        if not amount or amount <= 0:
            await update.message.reply_text(
                "🤔 Tôi không thấy số tiền rõ ràng. Bạn có thể nói cụ thể hơn không?\n\n" +
                "💡 Ví dụ: '5m lương tháng này' hoặc '1tr thưởng dự án'"
            )
            return
        
        # Sử dụng category từ AI hoặc fallback
        category = data.get('category')
        if not category:
            # Fallback nếu AI không trả về category
            if self.ai_service.is_enabled():
                category = self.ai_service.categorize_income(description)
            else:
                category = "Khác"
        
        # Lưu vào Google Sheets
        custom_date = data.get('custom_date')
        success = self._add_transaction_with_user_info(
            transaction_type="Thu",
            amount=amount,
            category=category,
            note=description,
            user_name=user_name,
            update=update,
            custom_date=custom_date
        )
        
        if success:
            from datetime import datetime
            from utils.date_utils import parse_custom_date
            
            # Hiển thị thời gian thực tế được ghi nhận  
            actual_datetime = parse_custom_date(custom_date)
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            
            if custom_date:
                date_info = f"📅 Ngày: {actual_datetime.strftime('%d/%m/%Y')} (ghi lúc {current_time})"
            else:
                date_info = f"📅 Thời gian: {current_time}"
            
            response = f"""
✅ Đã ghi nhận khoản thu vào {current_time}!

💰 Số tiền: {format_currency(amount)}
📂 Danh mục: {category} {"🤖" if self.ai_service.is_enabled() else ""}
📝 Ghi chú: {description}
{date_info}
👤 Người dùng: {user_name}

🔗 Xem chi tiết: {self._get_sheet_url(update)}
"""
        else:
            response = "🚫 Có lỗi khi lưu dữ liệu. Vui lòng thử lại!"
        
        await update.message.reply_text(response.strip())
    
    async def _handle_multiple_expenses(self, update: Update, data: Dict[str, Any], user_name: str):
        """Xử lý nhiều khoản chi khác danh mục"""
        transactions = data.get('transactions', [])
        
        if not transactions:
            await update.message.reply_text(
                "🤔 Tôi không thể tách được các khoản chi. Bạn có thể ghi từng khoản riêng được không?\n\n" +
                "💡 Ví dụ: Gửi 3 tin nhắn riêng:\n• '32k bún gà'\n• '1.5m laptop'\n• '200k xăng'"
            )
            return
        
        successful_transactions = []
        failed_transactions = []
        
        # Xử lý từng giao dịch
        for transaction in transactions:
            amount = transaction.get('amount', 0)
            description = transaction.get('description', '')
            category = transaction.get('category', 'Khác')
            custom_date = transaction.get('custom_date')  # Lấy custom_date từ từng transaction
            
            if amount > 0 and description:
                success = self._add_transaction_with_user_info(
                    transaction_type="Chi",
                    amount=amount,
                    category=category,
                    note=description,
                    user_name=user_name,
                    update=update,
                    custom_date=custom_date
                )
                
                if success:
                    successful_transactions.append({
                        'amount': amount,
                        'description': description,
                        'category': category,
                        'custom_date': custom_date
                    })
                else:
                    failed_transactions.append({
                        'amount': amount,
                        'description': description,
                        'category': category
                    })
        
        # Tạo response
        if successful_transactions:
            from datetime import datetime
            from utils.date_utils import parse_custom_date
            
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            
            # Kiểm tra xem có custom_date không
            first_custom_date = successful_transactions[0].get('custom_date')
            if first_custom_date:
                actual_datetime = parse_custom_date(first_custom_date)
                date_info = f"📅 Ngày: {actual_datetime.strftime('%d/%m/%Y')} (ghi lúc {current_time})"
                header_date = actual_datetime.strftime('%d/%m/%Y')
            else:
                date_info = f"📅 Thời gian: {current_time}"
                header_date = current_time.split()[1]  # Lấy phần ngày
            
            total_amount = sum(t['amount'] for t in successful_transactions)
            response = f"✅ **Đã ghi nhận {len(successful_transactions)} khoản chi vào {header_date}!**\n\n"
            
            for i, transaction in enumerate(successful_transactions, 1):
                response += f"{i}. 💸 {format_currency(transaction['amount'])}\n"
                response += f"   📂 {transaction['category']}\n"
                response += f"   📝 {transaction['description']}\n\n"
            
            response += f"💰 **Tổng cộng:** {format_currency(total_amount)}\n"
            response += f"{date_info}\n"
            response += f"👤 **Người dùng:** {user_name}\n\n"
            response += f"🔗 **Xem chi tiết:** {self._get_sheet_url(update)}"
            
            if failed_transactions:
                response += f"\n\n⚠️ **Có {len(failed_transactions)} khoản thất bại, vui lòng thử lại!**"
        else:
            response = "❌ Không thể ghi nhận khoản chi nào. Vui lòng thử lại!"
        
        await update.message.reply_text(response.strip())
    
    async def _handle_lending(self, update: Update, data: Dict[str, Any], user_name: str):
        """Xử lý khoản cho vay"""
        amount = data.get('amount')
        description = data.get('description', 'cho vay')
        person = data.get('person', 'N/A')
        
        if not amount or amount <= 0:
            await update.message.reply_text(
                "🤔 Tôi không thấy số tiền rõ ràng. Bạn có thể nói cụ thể hơn không?\n\n" +
                "💡 Ví dụ: 'cho An vay 2tr' hoặc 'cho bạn vay 1m'"
            )
            return
        
        # Category cố định cho lending
        category = "Cho vay"
        
        # Lưu vào Google Sheets
        custom_date = data.get('custom_date')
        success = self._add_transaction_with_user_info(
            transaction_type="Chi",  # Cho vay được tính là chi tiêu
            amount=amount,
            category=category,
            note=f"{description} (cho {person})",
            user_name=user_name,
            update=update,
            custom_date=custom_date
        )
        
        if success:
            from datetime import datetime
            from utils.date_utils import parse_custom_date
            
            # Hiển thị thời gian thực tế được ghi nhận  
            actual_datetime = parse_custom_date(custom_date)
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            
            if custom_date:
                date_info = f"📅 Ngày: {actual_datetime.strftime('%d/%m/%Y')} (ghi lúc {current_time})"
            else:
                date_info = f"📅 Thời gian: {current_time}"
            
            response = f"""
✅ Đã ghi nhận khoản cho vay vào {current_time}!

💸 Số tiền: {format_currency(amount)}
📂 Danh mục: {category}
👥 Cho vay: {person}
📝 Ghi chú: {description}
{date_info}
👤 Người dùng: {user_name}

🔗 Xem chi tiết: {self._get_sheet_url(update)}
"""
        else:
            response = "🚫 Có lỗi khi lưu dữ liệu. Vui lòng thử lại!"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_borrowing(self, update: Update, data: Dict[str, Any], user_name: str):
        """Xử lý khoản đi vay"""
        amount = data.get('amount')
        description = data.get('description', 'đi vay')
        person = data.get('person', 'N/A')
        
        if not amount or amount <= 0:
            await update.message.reply_text(
                "🤔 Tôi không thấy số tiền rõ ràng. Bạn có thể nói cụ thể hơn không?\n\n" +
                "💡 Ví dụ: 'vay anh Nam 1tr' hoặc 'mượn bạn 500k'"
            )
            return
        
        # Category cố định cho borrowing
        category = "Đi vay"
        
        # Lưu vào Google Sheets
        custom_date = data.get('custom_date')
        success = self._add_transaction_with_user_info(
            transaction_type="Thu",  # Đi vay được tính là thu nhập
            amount=amount,
            category=category,
            note=f"{description} (từ {person})",
            user_name=user_name,
            update=update,
            custom_date=custom_date
        )
        
        if success:
            from datetime import datetime
            from utils.date_utils import parse_custom_date
            
            # Hiển thị thời gian thực tế được ghi nhận  
            actual_datetime = parse_custom_date(custom_date)
            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
            
            if custom_date:
                date_info = f"📅 Ngày: {actual_datetime.strftime('%d/%m/%Y')} (ghi lúc {current_time})"
            else:
                date_info = f"📅 Thời gian: {current_time}"
            
            response = f"""
✅ Đã ghi nhận khoản đi vay vào {current_time}!

💰 Số tiền: {format_currency(amount)}
📂 Danh mục: {category}
👥 Vay từ: {person}
📝 Ghi chú: {description}
{date_info}
👤 Người dùng: {user_name}

🔗 Xem chi tiết: {self._get_sheet_url(update)}
"""
        else:
            response = "🚫 Có lỗi khi lưu dữ liệu. Vui lòng thử lại!"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_stats(self, update: Update, data: Dict[str, Any]):
        """Xử lý thống kê với AI data"""
        time_period = data.get('time_period', 'thang')
        specific_value = data.get('specific_value')
        
        try:
            # Tính toán khoảng thời gian dựa trên AI data
            if specific_value:
                start_date, end_date = self._get_date_range_with_specific_value(time_period, specific_value)
            else:
                start_date, end_date = self._get_date_range_for_period(time_period)
            
            # Lấy thống kê cho user này
            user_name = update.message.from_user.display_name or "Người dùng"
            user_id = update.message.from_user.id
            
            if self.user_sheet_manager:
                # Private mode - lấy từ sheet riêng của user
                user_service = self.user_sheet_manager.get_user_service(user_id)
                if not user_service:
                    await update.message.reply_text("❌ Bạn chưa thiết lập Google Sheet. Vui lòng gửi link sheet của bạn!")
                    return
                stats = user_service.get_statistics(user_name, start_date, end_date)
            else:
                # Shared mode - lấy từ sheet chung
                stats = self.sheets_service.get_statistics(user_name, start_date, end_date)
            
            # Format response với tên phù hợp
            if time_period == 'custom':
                # Khoảng thời gian tùy chỉnh
                period_name = f"từ {start_date.strftime('%d/%m')} đến {end_date.strftime('%d/%m')}"
            elif time_period == 'ngay' and specific_value:
                # Ngày cụ thể hoặc keywords
                if "/" in specific_value:
                    period_name = f"ngày {start_date.strftime('%d/%m/%Y')}"
                elif specific_value in ["hôm qua", "ngày hôm qua"]:
                    period_name = f"hôm qua ({start_date.strftime('%d/%m/%Y')})"
                elif specific_value in ["hôm kia", "ngày hôm kia"]:
                    period_name = f"hôm kia ({start_date.strftime('%d/%m/%Y')})"
                else:
                    period_name = f"ngày {start_date.strftime('%d/%m/%Y')}"
            else:
                period_name = {
                    'ngay': 'hôm nay',
                    'tuan': 'tuần này', 
                    'thang': 'tháng này',
                    'nam': 'năm này'
                }.get(time_period, 'khoảng thời gian')
            
            response = f"""
📊 THỐNG KÊ {period_name.upper()}
📅 {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}

💰 Tổng thu: {format_currency(stats['total_income'])}
💸 Tổng chi: {format_currency(stats['total_expense'])}
💵 Số dư: {format_currency(stats['balance'])}
📝 Giao dịch: {stats['transaction_count']}

🔗 Xem chi tiết: {self._get_sheet_url(update)}
"""
            
            await update.message.reply_text(response.strip())
            
        except Exception as e:
            logger.error(f"Lỗi tạo thống kê: {e}")
            await update.message.reply_text(
                f"🚫 Có lỗi khi tạo thống kê {period_name}. Vui lòng thử lại!"
            )
    
    async def _handle_help(self, update: Update):
        """Xử lý trợ giúp"""
        response = f"""
🤖 **BOT QUẢN LÝ THU CHI THÔNG MINH**

✨ **Tôi hiểu ngôn ngữ tự nhiên và tự động phân loại bằng AI!**

💸 **GHI CHI TIÊU:**
• `"500k trà sữa"` → Tự động phân loại "Ăn uống"
• `"hôm qua 200k xăng"` → Có thể ghi ngày cụ thể
• `"bún 50k, laptop 1.5m"` → Tự tách thành 2 giao dịch
• `"5/9 bánh 150k"` → Ghi cho ngày 5/9

💰 **GHI THU NHẬP:**
• `"5m lương"` → Ghi thu nhập
• `"nhận 1tr thưởng"` → AI hiểu từ khóa
• `"2/9 thưởng 500k"` → Thu nhập ngày cụ thể

📊 **XEM THỐNG KÊ:**
• `"thống kê"` → Tháng hiện tại
• `"thống kê hôm nay"` → Chỉ hôm nay
• `"thống kê hôm qua"` → Chỉ hôm qua
• `"thống kê tháng 8"` → Tháng cụ thể
• `"thống kê từ 1/8 đến 15/8"` → Khoảng tùy chỉnh

📈 **THỐNG KÊ DANH MỤC:**
• `"ăn uống"` → Chi tiêu ăn uống tháng này
• `"ăn uống hôm qua"` → Ăn uống ngày cụ thể
• `"top chi tiêu"` → Top 5 khoản chi lớn nhất
• `"danh mục"` → Xem tất cả danh mục

🎯 **DANH MỤC TỰ ĐỘNG:**
🍜 Ăn uống • 🛒 Mua sắm • ⛽ Di chuyển • 🏥 Y tế
🎮 Giải trí • 🏠 Sinh hoạt • 📚 Học tập • 👨‍👩‍👧‍👦 Gia đình

💡 **MẸO HAY:**
• Có thể ghi nhiều món: `"bún 12k, gà 20k, laptop 1.5m"`
• Hỗ trợ đơn vị: k (nghìn), m (triệu), tr (triệu)
• Hiểu ngày: hôm qua, hôm nay, 5/9, 2/10/2024

🚀 **Nói chuyện tự nhiên với tôi! Tôi sẽ hiểu và ghi chép cho bạn!**
"""
        
        await update.message.reply_text(response.strip())
    
    def _get_date_range_for_period(self, period: str):
        """Lấy khoảng thời gian theo period"""
        now = datetime.now()
        
        if period == 'ngay':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'tuan':
            # Tuần này (Thứ 2 đến Chủ nhật)
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'nam':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:  # 'thang'
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = now.replace(year=now.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
            else:
                end = now.replace(month=now.month+1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
        
        return start, end
    
    def _get_current_month_range(self):
        """Lấy khoảng thời gian tháng hiện tại"""
        return self._get_date_range_for_period('thang')
    
    def _get_date_range_with_specific_value(self, time_period: str, specific_value: str):
        """Xử lý khoảng thời gian với giá trị cụ thể từ AI"""
        now = datetime.now()
        
        if time_period == "custom" and "-" in specific_value:
            # Xử lý khoảng thời gian tùy chỉnh: "01/08-31/08"
            try:
                start_str, end_str = specific_value.split("-")
                
                # Parse ngày bắt đầu (dd/mm)
                if "/" in start_str:
                    start_day, start_month = map(int, start_str.split("/"))
                    start_year = now.year
                    start = datetime(start_year, start_month, start_day, 0, 0, 0)
                
                # Parse ngày kết thúc (dd/mm)
                if "/" in end_str:
                    end_day, end_month = map(int, end_str.split("/"))
                    end_year = now.year
                    end = datetime(end_year, end_month, end_day, 23, 59, 59, 999999)
                
                return start, end
            except Exception as e:
                logger.error(f"Lỗi parse custom date range: {specific_value}, {e}")
                # Fallback to current month
                return self._get_date_range_for_period('thang')
        
        elif specific_value == "thang_truoc":
            # Tháng trước
            if now.month == 1:
                prev_month = 12
                year = now.year - 1
            else:
                prev_month = now.month - 1
                year = now.year
            
            start = datetime(year, prev_month, 1)
            if prev_month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
            else:
                end = datetime(year, prev_month + 1, 1) - timedelta(microseconds=1)
            return start, end
            
        elif specific_value == "tuan_truoc":
            # Tuần trước
            days_since_monday = now.weekday()
            current_week_start = now - timedelta(days=days_since_monday)
            prev_week_start = current_week_start - timedelta(days=7)
            prev_week_end = prev_week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return prev_week_start.replace(hour=0, minute=0, second=0, microsecond=0), prev_week_end
            
        elif time_period == "ngay" and specific_value:
            # Xử lý ngày cho thống kê
            if "/" in specific_value:
                # Ngày cụ thể: "2/9", "15/8", "02/09"
                try:
                    if len(specific_value.split("/")) == 2:
                        day, month = map(int, specific_value.split("/"))
                        year = now.year
                        
                        # Tạo ngày cụ thể
                        target_date = datetime(year, month, day)
                        
                        # Nếu ngày trong tương lai của năm hiện tại, có thể là năm trước
                        if target_date > now:
                            target_date = datetime(year - 1, month, day)
                        
                        # Tạo khoảng thời gian cho cả ngày đó
                        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                        return start, end
                except Exception as e:
                    logger.error(f"Lỗi parse ngày cụ thể: {specific_value}, {e}")
            
            elif specific_value in ["hôm qua", "ngày hôm qua"]:
                # Hôm qua
                yesterday = now - timedelta(days=1)
                start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                return start, end
                
            elif specific_value in ["hôm kia", "ngày hôm kia"]:
                # Hôm kia
                day_before_yesterday = now - timedelta(days=2)
                start = day_before_yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end = day_before_yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                return start, end
                
        elif specific_value.isdigit():
            # Tháng cụ thể (số)
            month = int(specific_value)
            if 1 <= month <= 12:
                start = datetime(now.year, month, 1)
                if month == 12:
                    end = datetime(now.year + 1, 1, 1) - timedelta(microseconds=1)
                else:
                    end = datetime(now.year, month + 1, 1) - timedelta(microseconds=1)
                return start, end
        
        # Fallback to current period
        return self._get_date_range_for_period(time_period)
    
    async def _handle_help_guide(self, update: Update, context):
        """Xử lý tin nhắn không liên quan tài chính - trả lời hướng dẫn"""
        user_name = update.message.from_user.display_name or "bạn"
        
        response = f"""
👋 Xin chào {user_name}!

🤖 **Tôi là Bot Quản Lý Thu Chi AI - chỉ hỗ trợ về tài chính:**

💸 **VÍ DỤ CHI TIÊU:**
• `"500k trà sữa"` → Ăn uống
• `"hôm qua 200k xăng"` → Di chuyển (ngày cụ thể)
• `"bún 50k, laptop 1.5m"` → Tự tách 2 giao dịch

💰 **VÍ DỤ THU NHẬP:**
• `"5m lương"` → Lương
• `"nhận 1tr thưởng"` → Thưởng
• `"2/9 được 500k"` → Thu nhập ngày 2/9

📊 **VÍ DỤ THỐNG KÊ:**
• `"thống kê"` → Tháng này
• `"ăn uống hôm qua"` → Danh mục cụ thể
• `"top chi tiêu"` → Xếp hạng

✨ **TÍNH NĂNG ĐẶC BIỆT:**
🤖 AI tự động phân loại danh mục
📅 Hỗ trợ ghi ngày quá khứ
🔢 Tự động tách nhiều khoản trong 1 tin nhắn
📊 Thống kê chi tiết với biểu đồ

❓ **Cần trợ giúp chi tiết?** Nhắn `"help"` hoặc `"hướng dẫn"`

💡 **Hãy nói chuyện tự nhiên về tài chính với tôi!** 😊
"""
        
        await update.message.reply_text(response.strip())
    
    def _add_transaction_with_user_info(self, transaction_type: str, amount: float, 
                                      category: str, note: str, user_name: str, update: Update, custom_date: str = None) -> bool:
        """Helper method để thêm transaction với service phù hợp"""
        try:
            user_id = update.message.from_user.id
            
            if self.user_sheet_manager:
                # Private mode - sử dụng sheet riêng của user
                user_service = self.user_sheet_manager.get_user_service(user_id)
                if not user_service:
                    logger.error(f"❌ Không tìm thấy user service cho {user_name}")
                    return False
                
                return user_service.add_transaction(
                    transaction_type=transaction_type,
                    amount=amount,
                    category=category,
                    note=note,
                    user_name=user_name,
                    custom_date=custom_date
                )
            else:
                # Shared mode - sử dụng sheet chung
                return self.sheets_service.add_transaction(
                    transaction_type=transaction_type,
                    amount=amount,
                    category=category,
                    note=note,
                    user_name=user_name,
                    custom_date=custom_date
                )
        except Exception as e:
            logger.error(f"❌ Lỗi thêm transaction: {e}")
            return False
    
    async def _handle_setup_request(self, update: Update, context):
        """Yêu cầu user setup Google Sheet"""
        user_name = update.message.from_user.display_name or "bạn"
        setup_message = self.user_sheet_manager.generate_setup_message(user_name)
        await update.message.reply_text(setup_message.strip())
    
    async def _handle_sheet_setup(self, update: Update, context):
        """Xử lý setup Google Sheet từ user"""
        message_text = update.message.text
        user_name = update.message.from_user.display_name or "Người dùng"
        user_id = update.message.from_user.id
        
        # Thử thêm sheet cho user
        success = self.user_sheet_manager.add_user_sheet(user_id, user_name, message_text)
        
        if success:
            response = f"""
✅ **THIẾT LẬP THÀNH CÔNG!**

👤 User: {user_name}
📊 Google Sheet đã được kết nối!

🎉 **BẮT ĐẦU SỬ DỤNG:**
• "500k trà sữa" - Ghi chi tiêu
• "thu 5m lương" - Ghi thu nhập  
• "thống kê tháng này" - Xem báo cáo

🔒 **Bảo mật:** Chỉ bạn và bot mới truy cập được sheet này!
"""
        else:
            response = f"""
❌ **LỖI THIẾT LẬP!**

⚠️ Không thể kết nối đến Google Sheet của bạn.

🔧 **KIỂM TRA:**
• Link có đúng định dạng Google Sheets không?
• Đã chia sẻ với service account chưa?
• Sheet có tồn tại và truy cập được không?

💡 Hãy thử lại với link khác hoặc kiểm tra quyền truy cập!
"""
        
        await update.message.reply_text(response.strip())
    
    async def _handle_category_stats(self, update: Update, data: Dict[str, Any]):
        """Xử lý yêu cầu thống kê theo danh mục"""
        try:
            if self.user_sheet_manager:
                # Private mode
                user_id = update.message.from_user.id
                user_name = update.message.from_user.display_name or "Người dùng"
                
                if not self.user_sheet_manager.has_user_sheet(user_id):
                    await self._handle_setup_request(update, None)
                    return
                
                # Tạo sheets service cho user
                sheets_service = self.user_sheet_manager.get_user_service(user_id)
                if not sheets_service:
                    await update.message.reply_text(
                        "❌ Không thể kết nối đến Google Sheet của bạn. Vui lòng thiết lập lại!"
                    )
                    return
            else:
                # Shared mode
                sheets_service = self.sheets_service
            
            # Lấy thông tin từ AI data
            category_name = data.get('category_name', '')
            time_period = data.get('time_period', 'thang')
            specific_value = data.get('specific_value')
            
            # Import và gọi handler phù hợp
            if category_name:
                # Thống kê danh mục cụ thể với thời gian từ AI
                from handlers.stats_handler import handle_specific_category_stats_direct
                await handle_specific_category_stats_direct(update, sheets_service, category_name, time_period, specific_value)
            else:
                # Thống kê tất cả danh mục với thời gian từ AI
                from handlers.stats_handler import handle_category_stats_direct
                await handle_category_stats_direct(update, sheets_service, time_period, specific_value)
            
        except Exception as e:
            logger.error(f"Lỗi xử lý thống kê danh mục: {e}")
            await update.message.reply_text(
                "❌ Có lỗi xảy ra khi tạo thống kê danh mục. Vui lòng thử lại!"
            )
    
    async def _handle_category_list(self, update: Update):
        """Xử lý yêu cầu xem danh mục"""
        try:
            if self.user_sheet_manager:
                # Private mode
                user_id = update.message.from_user.id
                
                if not self.user_sheet_manager.has_user_sheet(user_id):
                    await self._handle_setup_request(update, None)
                    return
                
                # Tạo sheets service cho user
                sheets_service = self.user_sheet_manager.get_user_service(user_id)
                if not sheets_service:
                    await update.message.reply_text(
                        "❌ Không thể kết nối đến Google Sheet của bạn. Vui lòng thiết lập lại!"
                    )
                    return
            else:
                # Shared mode
                sheets_service = self.sheets_service
            
            # Import và gọi handler
            from handlers.stats_handler import handle_categories_direct
            await handle_categories_direct(update, sheets_service)
            
        except Exception as e:
            logger.error(f"Lỗi xử lý danh mục: {e}")
            await update.message.reply_text(
                "❌ Có lỗi xảy ra khi lấy danh mục. Vui lòng thử lại!"
            )
     

    def _get_sheet_url(self, update: Update) -> str:
        """Helper method để lấy sheet URL phù hợp với từng mode"""
        try:
            if self.user_sheet_manager:
                # Private mode - lấy URL sheet riêng của user
                user_id = update.message.from_user.id
                sheet_url = self.user_sheet_manager.get_user_sheet_url(user_id)
                return sheet_url or "Sheet riêng của bạn"
            else:
                # Shared mode - lấy URL sheet chung
                return self.sheets_service.get_sheet_url() if self.sheets_service else "Google Sheet"
        except Exception as e:
            logger.error(f"❌ Lỗi lấy sheet URL: {e}")
            return "Google Sheet" 
