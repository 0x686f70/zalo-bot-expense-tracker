# 🤖 Zalo Bot Thu Chi - AI Expense Tracker

**Bot Zalo thông minh để quản lý thu chi cá nhân với AI và Google Sheets**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![AI](https://img.shields.io/badge/AI-Gemini-green.svg)](https://ai.google.dev)
[![Sheets](https://img.shields.io/badge/Google-Sheets-yellow.svg)](https://sheets.google.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ **Tính Năng Nổi Bật**

### 🤖 **AI Thông Minh**
- **Natural Language Processing**: Hiểu ngôn ngữ tự nhiên hoàn toàn
- **Tự động phân loại**: AI phân loại danh mục thông minh (Ăn uống, Di chuyển, Y tế...)
- **Multi-item parsing**: Tự động tách nhiều khoản từ 1 tin nhắn
- **Smart date parsing**: Hỗ trợ ngày tùy chỉnh (hôm qua, 5/9, 2/10/2024)

### 💰 **Quản Lý Thu Chi**
- ✅ **Ghi chi tiêu**: `"500k trà sữa"`, `"bún 50k"`
- ✅ **Ghi thu nhập**: `"5m lương"`, `"nhận 1tr thưởng"`
- ✅ **Nhiều món cùng lúc**: `"bún 50k, laptop 1.5m, xăng 200k"` → Tự động tách 3 giao dịch
- ✅ **Ngày tùy chỉnh**: `"hôm qua 200k xăng"`, `"5/9 bánh 150k"`

### 📊 **Thống Kê Chi Tiết**
- ✅ **Tổng quan**: `"thống kê"`, `"thống kê hôm nay"`
- ✅ **Theo danh mục**: `"ăn uống"`, `"ăn uống tháng 8"`
- ✅ **Linh hoạt**: `"thống kê từ 1/8 đến 15/8"`
- ✅ **Top chi tiêu**: Hiển thị top 5 khoản chi lớn nhất với biểu đồ

### ⚡ **Performance & Reliability**
- **Caching thông minh**: Cache AI responses và Sheets data
- **API key rotation**: Tự động xoay API keys khi hết quota
- **Fast classification**: Regex-based cho queries đơn giản
- **Error handling**: Xử lý lỗi comprehensive với retry logic

---

## 🚀 **Quick Start (5 phút)**

### **1. Clone & Setup**
```bash
git clone https://github.com/yourusername/zalo-bot-thu-chi.git
cd zalo-bot-thu-chi

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Setup**
Tạo file `.env`:
```env
# Zalo Bot Token
ZALO_BOT_TOKEN=your_zalo_bot_token

# Gemini AI Keys (có thể dùng nhiều keys)
GEMINI_API_KEY=your_gemini_key_1
GEMINI_API_KEY_2=your_gemini_key_2
GEMINI_API_KEY_3=your_gemini_key_3

# Mode Configuration
PRIVATE_MODE=true  # true: mỗi user 1 sheet riêng
```

### **3. Google Sheets Setup**
```bash
# 1. Tạo Google Service Account: https://console.cloud.google.com/
# 2. Download credentials JSON → credentials/service-account.json
# 3. Tạo Google Sheet với header: Ngày | Loại | Số tiền | Mô tả | Danh mục
# 4. Share sheet với service account email (quyền Editor)
```

### **4. Zalo Bot Setup**
```bash
# 1. Tạo bot tại: https://developers.zalo.me/
# 2. Lấy bot token
# 3. Cập nhật webhook URL (sau khi chạy ngrok)
```

### **5. Run Bot**
```bash
# Terminal 1: Ngrok (expose local server)
ngrok http 8443

# Terminal 2: Bot
python main.py

# Terminal 3: Update webhook trên Zalo Developer Console
# URL: https://your-ngrok-url.ngrok.io/webhook
```

---

## 💬 **Cách Sử Dụng**

### **💸 Ghi Chi Tiêu**
```
"500k trà sữa"                    → 500,000 VNĐ, Ăn uống
"hôm qua 200k xăng"               → Custom date, Di chuyển  
"bún 50k, laptop 1.5m, xăng 200k" → 3 giao dịch riêng biệt
"5/9 bánh 150k"                   → Ngày cụ thể (5/9)
```

### **💰 Ghi Thu Nhập**
```
"5m lương"                        → 5,000,000 VNĐ, Lương
"nhận 1tr thưởng"                 → 1,000,000 VNĐ, Thưởng
"2/9 thưởng 500k"                 → Custom date
"bán hàng 800k"                   → Kinh doanh
```

### **📊 Xem Thống Kê**
```
"thống kê"                        → Tháng hiện tại
"thống kê hôm nay"                → Chỉ hôm nay
"thống kê hôm qua"                → Chỉ hôm qua
"thống kê tháng 8"                → Tháng cụ thể
"thống kê từ 1/8 đến 15/8"        → Custom range
```

### **📈 Thống Kê Danh Mục**
```
"ăn uống"                         → Chi tiêu ăn uống tháng này
"ăn uống hôm qua"                 → Ăn uống ngày cụ thể
"top chi tiêu"                    → Top 5 khoản chi lớn nhất
"danh mục"                        → Xem tất cả danh mục
```

### **❓ Trợ Giúp**
```
"help"                            → Hướng dẫn chi tiết
"hướng dẫn"                       → Hướng dẫn tiếng Việt
```

---

## 🎯 **Danh Mục Tự Động**

AI tự động phân loại vào các danh mục:

### **💸 Chi Tiêu**
- 🍜 **Ăn uống**: bún, phở, trà sữa, nướng, luộc, xào, cơm, bánh...
- 🛒 **Mua sắm**: áo, quần, giày, laptop, điện thoại, túi xách...
- ⛽ **Di chuyển**: xăng, taxi, grab, xe bus, vé máy bay...
- 🏥 **Y tế**: thuốc, khám bệnh, bảo hiểm y tế, vitamin...
- 🎮 **Giải trí**: phim, game, du lịch, karaoke, massage...
- 🏠 **Sinh hoạt**: điện, nước, internet, gas, thuê nhà...
- 📚 **Học tập**: sách, khóa học, học phí, đồ dùng học tập...
- 💼 **Công việc**: văn phòng phẩm, meeting, hội nghị...
- 👨‍👩‍👧‍👦 **Gia đình**: quà tặng, sinh nhật, đám cưới...

### **💰 Thu Nhập**
- 💼 **Lương**: lương, tiền lương, lương tháng...
- 🎁 **Thưởng**: thưởng, bonus, hoa hồng...
- 💰 **Kinh doanh**: bán hàng, lợi nhuận, doanh thu...
- 🎯 **Khác**: Thu nhập khác

---

## 🧪 **Testing**

### **📋 Test All Features**
```bash
python test_bot_features.py
```
**Expected Output:**
```
📊 PERFORMANCE SUMMARY (AI-Adjusted)
⚡ Average Response Time: 2.2s
🚀 Excellent (< 1.5s): 5
⚡ Good (1.5-2.5s): 25      ← Normal for AI!
⚠️ Acceptable (2.5-4.0s): 3
🐌 Slow (> 4.0s): 0

🎯 Overall Verdict: ⚡ GREAT! Good AI performance!
```

---

## ⚙️ **Configuration**

### **Environment Variables**
```env
# Required
ZALO_BOT_TOKEN=your_token
GEMINI_API_KEY=your_key

# Optional
GEMINI_API_KEY_2=backup_key_2
GEMINI_API_KEY_3=backup_key_3
PRIVATE_MODE=true
DEBUG=false
PORT=8443
```

### **Modes**
- **PRIVATE_MODE=true**: Mỗi user có Google Sheet riêng (recommended)
- **PRIVATE_MODE=false**: Tất cả user dùng chung 1 sheet

---

## 📁 **Project Structure**

```
zalo-bot-thu-chi/
├── 📱 main.py                    # Flask app chính
├── 📋 requirements.txt           # Dependencies  
├── 📖 README.md                  # Documentation
├── 📄 LICENSE                    # MIT License
├── 📝 env.example                # Environment template
├── 
├── 🤖 handlers/                  # Bot logic
│   ├── natural_language_handler.py  # AI xử lý ngôn ngữ tự nhiên
│   ├── stats_handler.py             # Thống kê & báo cáo  
│   ├── expense_handler.py           # Legacy expense handler
│   └── income_handler.py            # Legacy income handler
├── 
├── 🔧 services/                  # Core services
│   ├── natural_language_processor.py  # AI NLP engine
│   ├── gemini_ai.py                   # Gemini AI integration
│   ├── google_sheets.py               # Google Sheets API
│   ├── user_sheet_manager.py          # Multi-user management
│   └── api_key_manager.py             # API key rotation
├── 
├── 🛠️ utils/                     # Utilities
│   ├── date_utils.py             # Date parsing & calculation
│   └── format_utils.py           # Text formatting & display
├── 
├── 🧪 test_bot_features.py       # ✅ Comprehensive test script
├── 📁 credentials/               # Google Service Account (gitignored)
└── 📁 .venv/                     # Python virtual environment
```

---

## 🚀 **Performance**

### **⚡ Response Times (AI-Optimized)**
- **🚀 Excellent (< 1.5s)**: Cached responses, simple regex matches
- **⚡ Good (1.5-2.5s)**: Normal AI processing ← **Typical performance**
- **⚠️ Acceptable (2.5-4.0s)**: Complex multi-item processing
- **🐌 Slow (> 4.0s)**: API issues, needs investigation

### **🔧 Optimizations**
- **AI Response Caching**: 5-minute TTL for repeated queries
- **API Key Rotation**: Automatic failover when quota exceeded
- **Fast Classification**: Regex patterns for simple transactions
- **Batch Processing**: Efficient handling of multiple items
- **Performance Monitoring**: Real-time metrics and alerts

### **📊 Bottleneck Analysis**
- **🤖 AI API Calls**: 1.5-2.5s (primary bottleneck)
- **📊 Google Sheets API**: 0.2-0.5s (secondary)
- **⚙️ Bot Logic**: ~0.1s (minimal impact)

---

## 🔮 **Roadmap**

### **✅ Completed Features**
- ✅ Natural Language Processing với Gemini AI
- ✅ Automatic transaction splitting
- ✅ Custom date support (past dates)
- ✅ Smart category classification
- ✅ Comprehensive statistics with charts
- ✅ Performance optimization & caching
- ✅ Multi-user support (private sheets)
- ✅ Legacy command migration guides
- ✅ Comprehensive testing suite

### **🚧 Future Enhancements**
- 🔮 **Voice Message Support** (pending Zalo SDK update)
- 🔮 **Export to Excel/PDF reports**
- 🔮 **Budget planning & spending alerts**
- 🔮 **Multi-currency support**
- 🔮 **Recurring transactions**
- 🔮 **Advanced analytics & predictions**

---

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### **Development Setup**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python test_bot_features.py
python test_ai_performance.py

# Check performance
python performance_dashboard.py
```

---

## 🆘 **Support & Troubleshooting**

### **🔧 Common Issues**

#### **Bot không phản hồi**
```bash
# 1. Check bot health
curl http://localhost:8443/health

# 2. Verify ngrok URL
ngrok http 8443

# 3. Update webhook on Zalo Developer Console
```

#### **AI classification sai**
```bash
# Check API keys
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"

# Test bot features
python test_bot_features.py
```

#### **Google Sheets lỗi**
```bash
# Verify credentials
ls credentials/

# Check service account permissions
# Sheet must be shared with service account email
```

### **📊 Performance Issues**
```bash
# Test bot performance
python test_bot_features.py

# Check API key rotation
# Look for "API Key rotation" in logs

# Check bot logs for errors
tail -f main.py
```

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **[python-zalo-bot](https://github.com/zalo-bot/python-zalo-bot)**: Zalo Bot SDK
- **[Google Gemini AI](https://ai.google.dev/)**: Natural Language Processing
- **[Google Sheets API](https://developers.google.com/sheets)**: Data persistence
- **[Flask](https://flask.palletsprojects.com/)**: Web framework
- **[Ngrok](https://ngrok.com/)**: Local tunnel for webhooks

---

**🎉 Ready to manage your expenses intelligently with AI! Start chatting with your bot now! 🤖✨**

---

## 📞 **Contact**

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/zalo-bot-thu-chi/issues)
- **Discussions**: [Join community discussions](https://github.com/yourusername/zalo-bot-thu-chi/discussions)

---

*Made with ❤️ and 🤖 AI in Vietnam*