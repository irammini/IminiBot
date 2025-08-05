# IminiBot

IminiBot là một bot Discord đa tính năng thuộc dự án **Teaserverse**, được phát triển bởi `irammini` (Ngô Nhật Long). Đây là một dự án cá nhân, một sân chơi công nghệ để thử nghiệm các ý tưởng và công nghệ lập trình mới.

## 🤖 Giới thiệu

IminiBot là một bot thuộc thể loại "giải trí" với các tính năng đa dạng, tập trung vào tương tác và xây dựng một nền kinh tế ảo trong server Discord của bạn. Bot được xây dựng với mục tiêu học hỏi và sáng tạo, không có mục đích thương mại.

## ✨ Các tính năng chính

Dựa trên một hệ thống cơ sở dữ liệu PostgreSQL mạnh mẽ, IminiBot cung cấp một loạt các tính năng tương tác:

*   **Kinh tế & Xã hội:**
    *   **Ví & Ngân hàng:** Quản lý tài sản cá nhân (`wallet`, `bank_balance`).
    *   **Tương tác:** Xây dựng uy tín với hệ thống `!trust` và `!thank`.
    *   **Nhận thưởng:** `!daily` với hệ thống streak để khuyến khích sự tích cực.

*   **Phát triển Cá nhân:**
    *   **Hệ thống Việc làm:** Chọn một công việc (`jobs`), tăng điểm thành thạo (`mastery`) và mở khóa các kỹ năng (`job_skills`).
    *   **Nhiệm vụ:** Hoàn thành nhiệm vụ hàng ngày (`daily_quests`) và nhiệm vụ người dùng (`user_quests`) để nhận thưởng.
    *   **Thành tựu:** Mở khóa các thành tựu (`achievements`) ẩn và công khai.

*   **Tùy chỉnh & Cá nhân hóa:**
    *   **Profile Toàn diện:** Tùy chỉnh gần như mọi thứ: `about_me`, `custom_status`, `vibe_text`, màu sắc (`accent_color`), avatar, banner, và cả một trường tùy chỉnh riêng.
    *   **Moods:** Lưu và chuyển đổi giữa các bộ cấu hình profile khác nhau.
    *   **Imini ID:** Một định danh duy nhất trong hệ sinh thái Teaserverse.

*   **Giải trí & Sự kiện:**
    *   **Minigames:** Theo dõi tiến trình chơi game (`minigames`, `chaos_stats`).
    *   **Cửa hàng & Kho đồ:** Mua bán vật phẩm (`shop_items`, `inventory`) với các danh mục và độ hiếm khác nhau.
    *   **Giftcode:** Hệ thống giftcode linh hoạt với giới hạn sử dụng, thời gian hết hạn, và nhiều loại phần thưởng.
    *   **Sự kiện:** Tham gia các sự kiện toàn server (`events`).

## 🛠️ Công nghệ sử dụng

*   **Ngôn ngữ:** Python 3.x
*   **Framework:** Nextcord (một fork của discord.py) để tương tác với Discord API.
*   **Cơ sở dữ liệu:** PostgreSQL (sử dụng driver `asyncpg` cho thao tác bất đồng bộ).
*   **ORM & Migration:**
    *   **SQLAlchemy:** Core và ORM để làm việc với database một cách Pythonic.
    *   **Alembic:** Xử lý migration schema database một cách tự động và có phiên bản.
*   **Khác:**
    *   `python-dotenv`: Quản lý biến môi trường.
    *   `Pillow`: Xử lý và tạo hình ảnh.
    *   `requests`: Gửi các yêu cầu HTTP.

## 🚀 Bắt đầu

### Yêu cầu

*   Python 3.9+
*   Một server PostgreSQL đang hoạt động.
*   Git

### Hướng dẫn cài đặt

1.  **Clone repository:**
    ```bash
    git clone <repository_url>
    cd IminiBot
    ```

2.  **Thiết lập môi trường ảo:**
    *Nên sử dụng môi trường ảo để tránh xung đột thư viện.*
    ```bash
    # Tạo môi trường ảo
    python -m venv venv

    # Kích hoạt môi trường ảo
    # Trên Windows:
    venv\Scripts\activate
    # Trên Linux/macOS:
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Cấu hình biến môi trường:**
    Dự án sử dụng file `.env` để lưu các thông tin nhạy cảm. Hãy tạo một file tên là `.env` bên trong thư mục `IminiBot (main)/` với nội dung tương tự như sau:

    ```env
    # IminiBot (main)/.env

    # Token của Discord Bot
    DISCORD_TOKEN="your_discord_bot_token_here"

    # Chuỗi kết nối đến database PostgreSQL
    # Định dạng: postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
    DATABASE_URL="postgresql+asyncpg://postgres:your_password@localhost:5432/iminibot_db"
    ```
    *Lưu ý: Script Alembic (`alembic/env.py`) được cấu hình để đọc file `.env` từ đường dẫn này.*

5.  **Chạy Database Migrations:**
    Alembic sẽ đọc cấu hình từ `alembic.ini` và chuỗi kết nối database từ file `.env` bạn vừa tạo để thiết lập schema cho database.
    ```bash
    # Chạy lệnh này từ thư mục gốc của dự án (nơi chứa file alembic.ini)
    alembic upgrade head
    ```
    Lệnh này sẽ tạo tất cả các bảng cần thiết trong database của bạn.

6.  **Khởi chạy Bot:**
    ```bash
    python -m "IminiBot (main).main"
    ```
    Nếu mọi thứ được cấu hình chính xác, bot của bạn sẽ online!

## 📂 Cấu trúc dự án

Dưới đây là tổng quan về cấu trúc thư mục của dự án:

```
.
├── IminiBot (main)/    # Mã nguồn chính của bot
│   ├── cogs/           # Các module (cogs) của bot
│   ├── .env            # File cấu hình (bị ignore)
│   └── main.py         # Điểm khởi chạy bot
├── alembic/            # Các script migration của Alembic
│   ├── versions/       # Các file phiên bản migration
│   └── env.py          # Script cấu hình môi trường cho Alembic
├── shared/             # Các module chia sẻ
│   ├── db.py           # Định nghĩa Base cho SQLAlchemy
│   └── models/         # Các model của database
├── .gitignore
├── alembic.ini         # File cấu hình của Alembic
└── README.md
```

## 🗺️ Lộ trình phát triển

Phiên bản tiếp theo được mong đợi là **Huge Update 4.0: The Changed of The Era**, hứa hẹn sẽ mang đến những thay đổi lớn và "thời kỳ hoàng kim" cho IminiBot.

---
*Thông tin trong README này được tổng hợp từ `Teaserverse_document.json`.*