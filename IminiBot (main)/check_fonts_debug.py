import os
from PIL import ImageFont

def check_fonts():
    # 1️⃣ Xác định thư mục font tuyệt đối
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(script_dir, "fonts")

    print(f"📁 Thư mục hiện tại: {script_dir}")
    print(f"📁 Sẽ kiểm tra thư mục: {font_dir}\n")

    # 2️⃣ Kiểm tra thư mục tồn tại
    if not os.path.isdir(font_dir):
        print("❌ Không tìm thấy thư mục fonts.")
        return

    # 3️⃣ Liệt kê file trong thư mục
    files = os.listdir(font_dir)
    print(f"🗂️ Có {len(files)} file trong thư mục fonts:")
    print(files)
    print()

    # 4️⃣ Lọc .ttf
    ttf_files = [f for f in files if f.lower().endswith(".ttf")]
    if not ttf_files:
        print("⚠️ Không tìm thấy file .ttf nào.")
        return

    # 5️⃣ Thử mở từng font
    print("🔍 Kiểm tra khả năng mở font:\n")
    for fname in ttf_files:
        fpath = os.path.join(font_dir, fname)
        try:
            ImageFont.truetype(fpath, size=24)
            print(f"✅ Mở được: {fname}")
        except Exception as e:
            print(f"❌ Không mở được: {fname} → {type(e).__name__}: {e}")

# Gọi hàm test
check_fonts()