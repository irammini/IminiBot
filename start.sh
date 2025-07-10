#!/bin/bash

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
