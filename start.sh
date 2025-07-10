#!/bin/bash
echo "🔧 Hosting đã bắt đầu gọi start.sh"

echo "=============================="
echo "🚀 Khởi động IminiBot (v2.0)"
echo "=============================="

# 🧪 Kiểm tra .env
if [ ! -f ".env" ]; then
    echo "❌ Không tìm thấy file .env"
    exit 1
fi

# 📦 Cài thư viện từ requirements.txt nếu có
if [ -f "requirements.txt" ]; then
    echo "📦 Đang cài requirements.txt..."
    pip install --disable-pip-version-check -U --prefix .local -r requirements.txt
    echo "✅ Cài xong thư viện"
fi

# 🕒 Ghi log thời điểm khởi chạy
echo "🕒 Bắt đầu lúc: $(date)"

# 🚀 Khởi chạy bot.py
python3 bot.py  # Đảm bảo bot.py nằm ở thư mục gốc

echo "🏁 Bot đã khởi động hoặc kết thúc"
