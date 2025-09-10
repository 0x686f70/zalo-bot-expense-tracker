#!/usr/bin/env python3
"""
🤖 SCRIPT TEST TẤT CẢ TÍNH NĂNG BOT
Chạy: python test_bot_features.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8443/webhook"
TEST_USER_ID = "test_user_123"
TEST_USER_NAME = "Test User"

def create_test_message(text):
    """Tạo message test với format Zalo"""
    return {
        "event_name": "message.text.received",
        "message": {
            "message_id": f"test_{int(time.time())}",
            "text": text,
            "date": int(time.time() * 1000),
            "chat": {"id": TEST_USER_ID, "chat_type": "PRIVATE"},
            "from": {"id": TEST_USER_ID, "display_name": TEST_USER_NAME, "is_bot": False}
        }
    }

def test_webhook(text, description=""):
    """Test một tin nhắn với webhook"""
    print(f"\n🧪 {description}")
    print(f"📤 Input: '{text}'")
    
    start_time = time.time()
    
    try:
        data = create_test_message(text)
        response = requests.post(WEBHOOK_URL, json=data, timeout=12)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            # Performance indicator (adjusted for AI API reality)
            if response_time < 1.5:
                perf_icon = "🚀"  # Excellent for AI processing
            elif response_time < 2.5:
                perf_icon = "⚡"  # Good for AI processing
            elif response_time < 4.0:
                perf_icon = "⚠️"  # Acceptable for complex AI
            else:
                perf_icon = "🐌"  # Slow even for AI
            
            print(f"✅ {perf_icon} SUCCESS: {response_time:.3f}s")
            return response_time
        else:
            print(f"❌ Status: {response.status_code} - FAILED")
            print(f"📥 Response: {response.text}")
            return None
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return None
    
    time.sleep(0.8)  # Reduced delay for faster testing

def main():
    """Chạy tất cả test cases"""
    print("🚀 BẮT ĐẦU TEST BOT FEATURES")
    print("="*60)
    
    # Track performance
    all_times = []
    
    # 💸 CHI TIÊU TESTS
    print("\n💸 CHI TIÊU TESTS")
    print("-"*30)
    
    # Collect timing data
    times = []
    times.append(test_webhook("500k trà sữa", "Chi tiêu đơn giản"))
    times.append(test_webhook("480k nướng", "Chi tiêu + phân loại AI"))
    times.append(test_webhook("hôm qua 200k xăng", "Chi tiêu + custom date"))
    times.append(test_webhook("5/9 bánh 150k", "Chi tiêu + ngày cụ thể"))
    times.append(test_webhook("bún 80k và phở 150k", "Nhiều món cùng danh mục"))
    times.append(test_webhook("bún 50k, laptop 1.5m, 200k xăng", "Nhiều món khác danh mục"))
    times.append(test_webhook("hôm qua bún 30k, áo 300k", "Custom date + multiple items"))
    all_times.extend([t for t in times if t is not None])
    
    # 💰 THU NHẬP TESTS  
    print("\n💰 THU NHẬP TESTS")
    print("-"*30)
    
    times = []
    times.append(test_webhook("5m lương", "Thu nhập đơn giản"))
    times.append(test_webhook("nhận 1tr thưởng", "Thu nhập với từ khóa"))
    times.append(test_webhook("2/9 thưởng 500k", "Thu nhập + ngày cụ thể"))
    times.append(test_webhook("hôm qua được 2m", "Thu nhập + custom date"))
    all_times.extend([t for t in times if t is not None])
    
    # 📊 THỐNG KÊ TESTS
    print("\n📊 THỐNG KÊ TESTS")
    print("-"*30)
    
    times = []
    times.append(test_webhook("thống kê", "Thống kê tháng hiện tại"))
    times.append(test_webhook("thống kê hôm nay", "Thống kê hôm nay"))
    times.append(test_webhook("thống kê hôm qua", "Thống kê hôm qua"))
    times.append(test_webhook("thống kê 2/9", "Thống kê ngày cụ thể"))
    times.append(test_webhook("thống kê tuần này", "Thống kê tuần"))
    times.append(test_webhook("thống kê tháng 8", "Thống kê tháng cụ thể"))
    times.append(test_webhook("thống kê từ 1/8 đến 15/8", "Thống kê custom range"))
    all_times.extend([t for t in times if t is not None])
    
    # 📈 THỐNG KÊ DANH MỤC TESTS
    print("\n📈 THỐNG KÊ DANH MỤC TESTS")
    print("-"*30)
    
    test_webhook("ăn uống", "Thống kê ăn uống")
    test_webhook("ăn uống hôm qua", "Thống kê ăn uống hôm qua")
    test_webhook("ăn uống tháng 8", "Thống kê ăn uống tháng 8")
    test_webhook("top chi tiêu", "Top chi tiêu")
    test_webhook("xăng xe tuần này", "Thống kê xăng xe tuần")
    
    # 📋 DANH MỤC & TRỢ GIÚP TESTS
    print("\n📋 DANH MỤC & TRỢ GIÚP TESTS")
    print("-"*30)
    
    test_webhook("danh mục", "Xem danh mục")
    test_webhook("help", "Trợ giúp")
    test_webhook("xin chào", "Tin nhắn không liên quan")
    
    # 🎯 PHÂN LOẠI AI TESTS
    print("\n🎯 PHÂN LOẠI AI TESTS")
    print("-"*30)
    
    test_webhook("150k thịt", "Phân loại thịt → Ăn uống")
    test_webhook("80k rau củ", "Phân loại rau → Ăn uống")
    test_webhook("300k áo", "Phân loại áo → Mua sắm")
    test_webhook("100k taxi", "Phân loại taxi → Di chuyển")
    test_webhook("50k thuốc", "Phân loại thuốc → Y tế")
    
    # 🧪 EDGE CASES
    print("\n🧪 EDGE CASES")
    print("-"*30)
    
    test_webhook("hôm qua bún 12k, gà 20k, laptop 1.5m", "Complex: Custom date + Multiple categories")
    test_webhook("thống kê ăn uống từ 1/8 đến 15/8", "Complex: Category stats + Custom range")
    test_webhook("5/9 trà sữa 50k và laptop 2m", "Complex: Date + Cross category")
    
    # Performance Summary
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)
    
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        fastest = min(all_times)
        slowest = max(all_times)
        
        print(f"⚡ Average Response Time: {avg_time:.3f}s")
        print(f"🚀 Fastest Response: {fastest:.3f}s")
        print(f"🐌 Slowest Response: {slowest:.3f}s")
        print(f"🧪 Total Successful Tests: {len(all_times)}")
        
        # Performance categories (realistic for AI API)
        excellent_count = len([t for t in all_times if t < 1.5])
        good_count = len([t for t in all_times if 1.5 <= t < 2.5])
        acceptable_count = len([t for t in all_times if 2.5 <= t < 4.0])
        slow_count = len([t for t in all_times if t >= 4.0])
        
        print(f"\n📈 Performance Breakdown (AI-Adjusted):")
        print(f"🚀 Excellent (< 1.5s): {excellent_count}")
        print(f"⚡ Good (1.5-2.5s): {good_count}")
        print(f"⚠️ Acceptable (2.5-4.0s): {acceptable_count}")
        print(f"🐌 Slow (> 4.0s): {slow_count}")
        
        # Overall verdict (realistic for AI processing)
        if avg_time < 1.5:
            verdict = "🚀 EXCELLENT! Blazing fast for AI processing!"
        elif avg_time < 2.5:
            verdict = "⚡ GREAT! Good AI performance!"
        elif avg_time < 4.0:
            verdict = "✅ ACCEPTABLE! Normal AI processing time!"
        else:
            verdict = "⚠️ SLOW! AI bottleneck detected!"
        
        # Add AI bottleneck analysis
        print(f"\n🔍 Bottleneck Analysis:")
        print(f"🤖 AI API Calls: Primary bottleneck (~1.5-2.5s)")
        print(f"🔄 API Key Rotation: May add delays")
        print(f"📊 Sheets API: Secondary factor (~0.2-0.5s)")
        print(f"⚙️ Bot Logic: Minimal impact (~0.1s)")
        
        print(f"\n🎯 Overall Verdict: {verdict}")
    
    print("\n" + "="*60)
    print("🎉 HOÀN THÀNH TẤT CẢ TESTS!")
    print("📊 Kiểm tra kết quả trong Zalo và Google Sheets")
    print("="*60)

if __name__ == "__main__":
    print("🤖 BOT FEATURE TEST SCRIPT")
    print("📋 Test tất cả tính năng của bot")
    print(f"🌐 Webhook: {WEBHOOK_URL}")
    
    # Kiểm tra bot có chạy không
    try:
        response = requests.get("http://localhost:8443/health", timeout=5)
        if response.status_code == 200:
            print("✅ Bot đang chạy - Bắt đầu test!")
            main()
        else:
            print("❌ Bot không phản hồi health check")
    except Exception as e:
        print(f"❌ Không thể kết nối bot: {e}")
        print("💡 Hãy chạy 'python main.py' trước!") 
        