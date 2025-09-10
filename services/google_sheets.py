import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from performance_optimizer import cache_sheets_data, performance_optimizer

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Dịch vụ quản lý Google Sheets"""
    
    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.sheet_url = os.getenv('GOOGLE_SHEET_URL')
        
        if not self.credentials_path:
            raise ValueError("GOOGLE_CREDENTIALS_PATH không tìm thấy trong .env")
        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID không tìm thấy trong .env")
        if not self.sheet_url:
            raise ValueError("GOOGLE_SHEET_URL không tìm thấy trong .env")
            
        self._setup_client()
    
    def _setup_client(self):
        """Thiết lập client Google Sheets"""
        try:
            # Cấu hình scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Tạo credentials từ file JSON
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scopes
            )
            
            # Khởi tạo client
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            # Không tạo worksheet mặc định nữa - sẽ tạo theo user
            logger.info("✅ Google Sheets client đã sẵn sàng - Multi-user mode")
                
        except Exception as e:
            logger.error(f"Lỗi thiết lập Google Sheets client: {e}")
            raise
    
    def _get_or_create_user_worksheet(self, user_name: str):
        """Lấy hoặc tạo worksheet cho user"""
        try:
            # Normalize tên user (loại bỏ ký tự đặc biệt)
            safe_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not safe_name:
                safe_name = "Unknown_User"
            
            # Giới hạn độ dài tên worksheet (Google Sheets limit)
            if len(safe_name) > 100:
                safe_name = safe_name[:97] + "..."
            
            try:
                # Thử lấy worksheet có sẵn
                worksheet = self.spreadsheet.worksheet(safe_name)
                logger.info(f"📋 Sử dụng worksheet có sẵn: {safe_name}")
                return worksheet
            except gspread.WorksheetNotFound:
                # Tạo worksheet mới cho user
                logger.info(f"🆕 Tạo worksheet mới cho user: {safe_name}")
                worksheet = self.spreadsheet.add_worksheet(
                    title=safe_name,
                    rows="1000",
                    cols="10"
                )
                # Thêm header
                worksheet.append_row([
                    "Ngày", "Loại", "Số tiền", "Danh mục", "Ghi chú"
                ])
                return worksheet
                
        except Exception as e:
            logger.error(f"Lỗi tạo/lấy worksheet cho user {user_name}: {e}")
            raise

    def test_connection(self):
        """Test kết nối Google Sheets"""
        try:
            # Test bằng cách lấy thông tin spreadsheet
            sheet_title = self.spreadsheet.title
            logger.info(f"✅ Test kết nối thành công. Spreadsheet: {sheet_title}")
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi test kết nối: {e}")
            raise
    
    def add_transaction(self, transaction_type: str, amount: float, category: str, 
                       note: str, user_name: str, custom_date: str = None) -> bool:
        """
        Thêm giao dịch mới vào worksheet riêng của user
        
        Args:
            transaction_type: 'Thu' hoặc 'Chi'
            amount: Số tiền
            category: Danh mục
            note: Ghi chú
            user_name: Tên người dùng (display_name)
            custom_date: Ngày tùy chỉnh (VD: "5/9", "hôm qua", null)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Lấy worksheet riêng cho user này
            user_worksheet = self._get_or_create_user_worksheet(user_name)
            
            # Chuẩn bị dữ liệu (không cần user_name nữa vì đã có worksheet riêng)
            from utils.date_utils import parse_custom_date
            
            # Parse custom date hoặc sử dụng thời gian hiện tại
            target_datetime = parse_custom_date(custom_date)
            formatted_time = target_datetime.strftime("%d/%m/%Y %H:%M:%S")
            
            row_data = [
                formatted_time,
                transaction_type,
                amount,
                category,
                note
            ]
            
            # Thêm vào worksheet của user
            user_worksheet.append_row(row_data)
            
            logger.info(f"👤 {user_name}: {transaction_type} - {amount:,.0f} VNĐ - {category}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi thêm giao dịch cho {user_name}: {e}")
            return False
    
    def get_transactions(self, user_name: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """
        Lấy danh sách giao dịch theo khoảng thời gian từ worksheet của user
        
        Args:
            user_name: Tên người dùng
            start_date: Ngày bắt đầu
            end_date: Ngày kết thúc
            
        Returns:
            List[Dict]: Danh sách giao dịch
        """
        try:
            # Lấy worksheet của user
            user_worksheet = self._get_or_create_user_worksheet(user_name)
            
            # Lấy tất cả dữ liệu từ worksheet của user
            all_records = user_worksheet.get_all_records()
            
            if not all_records:
                return []
            
            transactions = []
            
            for record in all_records:
                try:
                    # Parse ngày từ string
                    date_str = record.get('Ngày', '')
                    if not date_str:
                        continue
                    
                    # Xử lý format ngày (có thể có giờ)
                    if ' ' in date_str:
                        date_part = date_str.split(' ')[0]
                    else:
                        date_part = date_str
                    
                    transaction_date = datetime.strptime(date_part, "%d/%m/%Y")
                    
                    # Lọc theo khoảng thời gian
                    if start_date and transaction_date < start_date:
                        continue
                    if end_date and transaction_date > end_date:
                        continue
                    
                    # Chuẩn hóa số tiền
                    amount = 0
                    if record.get('Số tiền'):
                        try:
                            amount = float(str(record['Số tiền']).replace(',', ''))
                        except:
                            amount = 0
                    
                    transaction = {
                        'date': transaction_date,
                        'type': record.get('Loại', ''),
                        'amount': amount,
                        'category': record.get('Danh mục', ''),
                        'note': record.get('Ghi chú', ''),
                        'user': record.get('Người dùng', '')
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Lỗi parse giao dịch: {record}, Error: {e}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.error(f"Lỗi lấy giao dịch: {e}")
            return []
    
    def get_categories(self) -> Dict[str, List[str]]:
        """
        Lấy danh sách danh mục theo loại giao dịch
        
        Returns:
            Dict: {'Thu': [...], 'Chi': [...]}
        """
        try:
            all_records = self.worksheet.get_all_records()
            categories = {'Thu': set(), 'Chi': set()}
            
            for record in all_records:
                transaction_type = record.get('Loại', '')
                category = record.get('Danh mục', '')
                
                if transaction_type in categories and category:
                    categories[transaction_type].add(category)
            
            # Convert set to sorted list
            return {
                'Thu': sorted(list(categories['Thu'])),
                'Chi': sorted(list(categories['Chi']))
            }
            
        except Exception as e:
            logger.error(f"Lỗi lấy danh mục: {e}")
            return {'Thu': [], 'Chi': []}
    
    def get_statistics(self, user_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Tính toán thống kê thu chi cho user cụ thể
        
        Args:
            user_name: Tên người dùng
            start_date: Ngày bắt đầu
            end_date: Ngày kết thúc
            
        Returns:
            Dict: Thống kê chi tiết
        """
        try:
            transactions = self.get_transactions(user_name, start_date, end_date)
            
            if not transactions:
                return {
                    'total_income': 0,
                    'total_expense': 0,
                    'balance': 0,
                    'income_categories': {},
                    'expense_categories': {},
                    'transaction_count': 0
                }
            
            total_income = 0
            total_expense = 0
            income_categories = defaultdict(float)
            expense_categories = defaultdict(float)
            
            for transaction in transactions:
                amount = transaction['amount']
                category = transaction['category']
                
                if transaction['type'] == 'Thu':
                    total_income += amount
                    income_categories[category] += amount
                elif transaction['type'] == 'Chi':
                    total_expense += amount
                    expense_categories[category] += amount
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': total_income - total_expense,
                'income_categories': dict(income_categories),
                'expense_categories': dict(expense_categories),
                'transaction_count': len(transactions),
                'start_date': start_date,
                'end_date': end_date
            }
            
        except Exception as e:
            logger.error(f"Lỗi tính thống kê: {e}")
            return {
                'total_income': 0,
                'total_expense': 0,
                'balance': 0,
                'income_categories': {},
                'expense_categories': {},
                'transaction_count': 0
            }
    
    def get_sheet_url(self) -> str:
        """Lấy URL của Google Sheet"""
        return self.sheet_url