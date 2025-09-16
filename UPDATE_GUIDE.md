# 🔄 HƯỚNG DẪN UPDATE DỰ ÁN ĐANG CHẠY

## 📋 CÁCH 1: UPDATE TRỰC TIẾP (Khuyến nghị)

Nếu dự án đang chạy trên server/local:

### 1. Dừng bot hiện tại:
```bash
# Nếu chạy trong terminal
Ctrl+C

# Hoặc kill process
ps aux | grep python
kill <process_id>
```

### 2. Pull code mới nhất:
```bash
git pull origin main
```

### 3. Khởi động lại bot:
```bash
python main.py
```

---

## 📋 CÁCH 2: UPDATE VỚI DOCKER

### 1. Dừng container:
```bash
docker-compose down
```

### 2. Pull code mới:
```bash
git pull origin main
```

### 3. Rebuild và restart:
```bash
docker-compose up --build -d
```

---

## 📋 CÁCH 3: ZERO-DOWNTIME UPDATE (Production)

### 1. Clone repo mới vào thư mục tạm:
```bash
git clone https://github.com/0x686f70/zalo-bot-expense-tracker.git temp-update
```

### 2. Copy config files:
```bash
cp .env temp-update/
cp -r credentials/* temp-update/credentials/
cp user_sheets.json temp-update/ 2>/dev/null || true
```

### 3. Test trong thư mục tạm:
```bash
cd temp-update
python main.py
# Test xem bot có hoạt động không
# Ctrl+C để dừng test
```

### 4. Nếu OK, thay thế code hiện tại:
```bash
cd ..
mv zalo-bot-thu-chi old-version
mv temp-update zalo-bot-thu-chi
cd zalo-bot-thu-chi
python main.py
```

---

## ✅ XÁC MINH UPDATE THÀNH CÔNG

### Test các tính năng mới:

1. **Test LENDING:**
   ```
   Gửi: "cho bạn vay 1tr"
   Expect: Bot trả lời với category "Cho vay"
   ```

2. **Test BORROWING:**
   ```
   Gửi: "vay An 500k"
   Expect: Bot trả lời với category "Đi vay"
   ```

3. **Test câu phức tạp:**
   ```
   Gửi: "cho bạn vay 10tr trong đó 6tr tiền nhà, 4tr tiền tiết kiệm"
   Expect: Bot hiểu được và ghi 10tr với category "Cho vay"
   ```

### Kiểm tra Google Sheets:
- Mở Google Sheets
- Kiểm tra có ghi transaction với category "Cho vay" hoặc "Đi vay"

---

## 🚨 LƯU Ý QUAN TRỌNG

1. **Backup trước khi update:**
   ```bash
   cp .env .env.backup
   cp -r credentials/ credentials_backup/
   cp user_sheets.json user_sheets_backup.json 2>/dev/null || true
   ```

2. **Nếu có lỗi, rollback:**
   ```bash
   git reset --hard HEAD~1
   # Hoặc restore từ backup
   ```

3. **Kiểm tra logs:**
   ```bash
   tail -f logs/bot.log
   # Hoặc xem console output
   ```

## 🎯 Tính năng mới có gì?

- ✅ **LENDING**: Xử lý "cho vay", "cho mượn"
- ✅ **BORROWING**: Xử lý "vay tiền", "mượn tiền"  
- ✅ **Person tracking**: Biết ai vay, ai cho vay
- ✅ **Complex parsing**: Hiểu câu phức tạp như của bạn
- ✅ **Auto categorization**: Tự động phân loại "Cho vay"/"Đi vay" 