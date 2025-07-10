#!/bin/bash

<<<<<<< HEAD
echo "=============================="
echo "🚀 Khởi động IminiBot (v2.0)"
echo "=============================="

# 🧪 Kiểm tra file .env tồn tại
if [ ! -f ".env" ]; then
    echo "❌ Không tìm thấy file .env"
    exit 1
fi

# 🧠 Cài thư viện từ requirements.txt nếu tồn tại
if [ -f "requirements.txt" ]; then
    echo "📦 Đang cài thư viện từ requirements.txt..."
    pip install --disable-pip-version-check -U --prefix .local -r requirements.txt
    echo "✅ Cài xong requirements.txt"
fi

# ⏱️ Log thời điểm khởi chạy
echo "🕒 Khởi chạy lúc: $(date)"

# 🔥 Chạy bot
echo "🔧 Chạy file bot.py"
python3 bot.py  # ➤ Nếu chắc hosting dùng Python 3 mặc định, bạn có thể đổi thành: python bot.py

echo "🏁 Bot đã khởi động (hoặc đã dừng)"
=======
echo "==========================="
echo "🚀 Đang khởi động IminiBot..."
echo "==========================="

# 🧠 Cài thư viện từ requirements.txt nếu file tồn tại
if [ -f "requirements.txt" ]; then
    echo "📦 Đang cài thư viện từ requirements.txt..."
    pip install --disable-pip-version-check -U --prefix .local -r requirements.txt
    echo "✅ Cài thư viện hoàn tất!"
else
    echo "⚠️ Không tìm thấy requirements.txt, bỏ qua bước cài thư viện."
fi

# 💡 Ghi lại thời gian khởi động
echo "⏱️ Thời điểm khởi động: $(date)"

# 🔥 Khởi động bot từ file chính
echo "🚀 Đang chạy: IminiBot_main/main.py"
python3 IminiBot_main/main.py

echo "🏁 Bot đã chạy xong hoặc gặp lỗi. Kiểm tra log để biết thêm chi tiết."
>>>>>>> f77288b49554ac0cdee11a575116e02c654b2b03
