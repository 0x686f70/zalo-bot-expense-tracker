from flask import Flask, request
from zalo_bot import Bot, Update
from zalo_bot.ext import Dispatcher, CommandHandler, MessageHandler, filters
from zalo_bot.constants import ChatAction
import os
from dotenv import load_dotenv
import logging
import asyncio

# Import handlers
from handlers.income_handler import handle_income
from handlers.expense_handler import handle_expense  
from handlers.stats_handler import handle_stats, handle_categories, handle_category_stats
from handlers.natural_language_handler import NaturalLanguageHandler
from services.google_sheets import GoogleSheetsService
from services.user_sheet_manager import UserSheetManager

# Load environment variables
load_dotenv()

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Khởi tạo Flask app
app = Flask(__name__)

# Cấu hình bot
TOKEN = os.getenv('ZALO_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PRIVATE_MODE = os.getenv('PRIVATE_MODE', 'false').lower() == 'true'
SECRET_TOKEN = os.getenv('SECRET_TOKEN', 'default_secret')
PORT = int(os.getenv('PORT', 8443))

if not TOKEN:
    raise ValueError("ZALO_BOT_TOKEN không được tìm thấy trong file .env")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL không được tìm thấy trong file .env")

# Khởi tạo bot và services
bot = Bot(token=TOKEN)

# Khởi tạo services
if PRIVATE_MODE:
    logger.info("🔒 Khởi động chế độ PRIVATE - User tự cung cấp Google Sheet")
    user_sheet_manager = UserSheetManager()
    sheets_service = None  # Sẽ tạo động cho từng user
else:
    logger.info("🌐 Khởi động chế độ SHARED - Tất cả dùng chung Google Sheet")
    user_sheet_manager = None
    sheets_service = GoogleSheetsService()

nl_handler = NaturalLanguageHandler(sheets_service, user_sheet_manager)

# Hàm xử lý lệnh /start
async def start_command(update: Update, context):
    """Xử lý lệnh /start"""
    # Hiển thị "đang soạn tin..." 
    await context.bot.send_chat_action(
        chat_id=update.message.chat.id,
        action=ChatAction.TYPING
    )
    
    user_name = update.effective_user.display_name or "bạn"
    welcome_message = f"""
🤖 Xin chào {user_name}! Chào mừng bạn đến với Bot Quản lý Thu Chi thông minh!

🆕 **NÂNG CẤP MỚI - NGÔN NGỮ TỰ NHIÊN:**

💸 **Ghi chi tiêu:**
• "500k trà sữa"
• "200k xăng"
• "mua áo 300k"

💰 **Ghi thu nhập:**
• "5m lương"
• "nhận 1tr"
• "được 500k"

📊 **Xem thống kê:**
• "thống kê" - Tổng quan
• "top chi tiêu" - Top 5 chi nhiều nhất
• "ăn uống" - Chi tiết danh mục
• "danh mục" - Xem tất cả danh mục

🤖 **Tính năng AI:**
• Hiểu ngôn ngữ tự nhiên
• Tự động phân loại danh mục
• Phản hồi thông minh

💡 **Lệnh cũ vẫn dùng được:** /chi, /thu, /thongke, /danhmuc, /thongkedanhmuc
❓ **Trợ giúp:** "help" hoặc /help

🔗 Google Sheet: {sheets_service.get_sheet_url()}
    """
    await update.message.reply_text(welcome_message.strip())

# Hàm xử lý lệnh /help
async def help_command(update: Update, context):
    """Xử lý lệnh /help"""
    await start_command(update, context)

# Hàm xử lý tin nhắn không phải lệnh (Natural Language)
async def handle_natural_language(update: Update, context):
    """Xử lý tin nhắn bằng ngôn ngữ tự nhiên"""
    try:
        # Sử dụng Natural Language Handler
        result = await nl_handler.handle_natural_message(update, context)
        return result
    except Exception as e:
        logger.error(f"Lỗi xử lý natural language: {e}")
        return None

# Thiết lập webhook khi ứng dụng khởi động
with app.app_context():
    try:
        logger.info("🔗 THIẾT LẬP WEBHOOK:")
        logger.info(f"   🌐 URL: {WEBHOOK_URL}")
        bot.set_webhook(url=WEBHOOK_URL, secret_token=SECRET_TOKEN)
        logger.info("   ✅ Webhook đã được thiết lập thành công!")
    except Exception as e:
        logger.error(f"   ❌ Lỗi thiết lập webhook: {e}")

# Khởi tạo dispatcher và đăng ký handlers
dispatcher = Dispatcher(bot, None, workers=0)

# Đăng ký command handlers
dispatcher.add_handler(CommandHandler('start', start_command))
dispatcher.add_handler(CommandHandler('help', help_command))
# Wrapper functions for proper async handling
async def handle_income_wrapper(update, context):
    return await handle_income(update, context, sheets_service)

async def handle_expense_wrapper(update, context):
    return await handle_expense(update, context, sheets_service)

async def handle_stats_wrapper(update, context):
    return await handle_stats(update, context, sheets_service)

async def handle_categories_wrapper(update, context):
    return await handle_categories(update, context, sheets_service)

async def handle_category_stats_wrapper(update, context):
    return await handle_category_stats(update, context, sheets_service)

dispatcher.add_handler(CommandHandler('thu', handle_income_wrapper))
dispatcher.add_handler(CommandHandler('chi', handle_expense_wrapper))
dispatcher.add_handler(CommandHandler('thongke', handle_stats_wrapper))
dispatcher.add_handler(CommandHandler('danhmuc', handle_categories_wrapper))
dispatcher.add_handler(CommandHandler('thongkedanhmuc', handle_category_stats_wrapper))

# Đăng ký message handler cho tin nhắn thường (Natural Language)
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_language))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Bot is running"}, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint webhook để nhận tin nhắn từ Zalo"""
    try:
        # Lấy dữ liệu từ request
        json_data = request.get_json(force=True)
        logger.info(f"Nhận webhook: {json_data}")
        
        # Parse update từ JSON
        if 'result' in json_data:
            update = Update.de_json(json_data['result'], bot)
        else:
            update = Update.de_json(json_data, bot)
        
        # Xử lý update đồng bộ - cách đơn giản và hiệu quả
        dispatcher.process_update(update)
        
        return {'status': 'ok'}, 200
        
    except Exception as e:
        logger.error(f"Lỗi xử lý webhook: {e}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/')
def home():
    """Trang chủ"""
    return """
    <h1>Zalo Bot Quản lý Thu Chi</h1>
    <p>Bot đang hoạt động!</p>
    <p><a href="/health">Kiểm tra trạng thái</a></p>
    """

def print_startup_info():
    """In thông tin khởi tạo bot"""
    print("\n" + "="*60)
    print("🤖 ZALO BOT QUẢN LÝ THU CHI")
    print("🚀 Phiên bản: 2.0 - AI Powered")
    print("="*60)
    
    # Thông tin cấu hình
    logger.info("📋 THÔNG TIN CẤU HÌNH:")
    logger.info(f"   🌐 Webhook URL: {WEBHOOK_URL}")
    logger.info(f"   🔌 Port: {PORT}")
    logger.info(f"   🔧 Debug Mode: {os.getenv('DEBUG', 'False')}")
    logger.info(f"   🔒 Private Mode: {'✅ BẬT' if PRIVATE_MODE else '❌ TẮT'}")
    
    # Kiểm tra Google Sheets
    logger.info("📊 KIỂM TRA GOOGLE SHEETS:")
    try:
        if PRIVATE_MODE:
            stats = user_sheet_manager.get_stats()
            logger.info("   ✅ User Sheet Manager đã sẵn sàng!")
            logger.info(f"   👥 Đã có {stats['total_users']} user đăng ký")
            logger.info("   🔒 User tự cung cấp Google Sheet riêng")
        else:
            sheets_service.test_connection()
            logger.info("   ✅ Kết nối Google Sheets thành công!")
            logger.info(f"   📄 Sheet URL: {sheets_service.get_sheet_url()}")
    except Exception as e:
        logger.error(f"   ❌ Lỗi kiểm tra Google Sheets: {e}")
    
    # Kiểm tra Gemini AI
    logger.info("🤖 KIỂM TRA GEMINI AI:")
    try:
        from services.gemini_ai import GeminiAIService
        ai_service = GeminiAIService()
        if ai_service.is_enabled():
            logger.info("   ✅ Gemini AI đã được kích hoạt!")
            logger.info("   🧠 Tính năng: Phân loại danh mục tự động")
            
            # Hiển thị thông tin API keys
            status = ai_service.get_api_status()
            logger.info(f"   🔑 API Keys: {status['available_keys']}/{status['total_keys']} khả dụng")
            logger.info(f"   🎯 Đang dùng: {ai_service.get_current_key_info()}")
            
            if status['cooldown_keys'] > 0:
                logger.warning(f"   ⏰ Cooldown: {status['cooldown_keys']} keys")
        else:
            logger.warning("   ⚠️  Gemini AI chưa được kích hoạt (thiếu API keys)")
            logger.info("   🔧 Sử dụng: Phân loại từ khóa cơ bản")
    except Exception as e:
        logger.error(f"   ❌ Lỗi kiểm tra Gemini AI: {e}")
    
    print("="*60)
    logger.info("🎉 BOT ĐÃ SẴN SÀNG HOẠT ĐỘNG!")
    print("="*60 + "\n")

if __name__ == '__main__':
    # In thông tin khởi tạo
    print_startup_info()
    
    # Chạy Flask app
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )