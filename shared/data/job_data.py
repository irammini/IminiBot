JOB_DATA = {
    # ⚒️ Nhóm sản xuất & công nghiệp
    "cn": {
        "name": "Công nhân",
        "description": "Nghề dành cho người thất nghiệp!",
        "category": "industry",
        "emoji": "🧱",
        "base_pay": 1000,
        "level_required": 15,
        "skills": {
            "grit_up": ("🧱 Bền Bỉ Vượt Mọi Deadline", "Tăng thu nhập từ `!work` thêm 5% mỗi cấp", 5),
            "stress_resist": ("🧱 Kháng Stress", "Giảm cooldown `!work` mỗi cấp 2s", 5)
        }
    },
    "cn_manager": {
        "name": "Quản lý công nhân",
        "description": "Quản lý những người thất nghiệp...",
        "category": "industry",
        "emoji": "🏭",
        "base_pay": 5000,
        "level_required": 20
    },

    # 💼 Nhóm văn phòng
    "os": {
        "name": "Nhân viên văn phòng",
        "description": "Chuẩn bị bán mình cho tư bản nào!",
        "category": "office",
        "emoji": "🧑‍💻",
        "base_pay": 15000,
        "level_required": 25,
        "skills": {
            "deadline_dodge": ("🧑‍💻 Né Deadline", "Miễn cooldown `!work` 1 lần/ngày", 1),
            "pay_raise": ("🧑‍💻 Trả Lương Mạnh Tay", "Tăng base pay `!work` thêm 50 mỗi cấp", 3)
        }
    },
    "os_manager": {
        "name": "Quản lý văn phòng",
        "description": "Thay vì bán mình cho tư bản, ta có bán mình cho deadline!?",
        "category": "office",
        "emoji": "📈",
        "base_pay": 100000,
        "level_required": 40
    },

    # 🎨 Nhóm sáng tạo
    "cc": {
        "name": "Nhà sáng tạo nội dung",
        "description": "Làm cho công ty của bạn từ vô danh thành nổi tiếng!",
        "category": "creative",
        "emoji": "🎨",
        "base_pay": 200000,
        "level_required": 60,
        "skills": {
            "viral_boost": ("🎨 Bùng Nổ Truyền Thông", "Tạo item đặc biệt mỗi 7 ngày", 1),
            "idea_combo": ("🎨 Chuỗi Ý Tưởng", "`!work` 3 ngày liên tục → thêm 500 xu", 3)
        }
    },
    "cd": {
        "name": "Giám đốc công ty",
        "description": "Người quản lý tất cả",
        "category": "creative",
        "emoji": "🧑‍✈️",
        "base_pay": 500000,
        "level_required": 100
    },

        "ux_designer": {
        "name": "Thiết kế trải nghiệm",
        "description": "Thiết kế trải nghiệm người chơi, ngay cả khi emoji không phản hồi như mong đợi.",
        "category": "creative",
        "emoji": "🎨",
        "base_pay": 110000,
        "level_required": 42
    },

    "content_writer": {
        "name": "Biên tập nội dung",
        "description": "Viết mọi bản mô tả — kể cả cho badge không có ai mở được.",
        "category": "creative",
        "emoji": "📝",
        "base_pay": 100000,
        "level_required": 40
    },

    # 🎮 Nhóm game thủ / streamer
    "gamer": {
        "name": "Game thủ chuyên nghiệp",
        "description": "Minigame là cuộc sống!",
        "category": "entertainment",
        "emoji": "🎮",
        "base_pay": 5000,
        "level_required": 20,
        "skills": {
            "minigame_mastery": ("🎮 Phản Xạ Game", "Tăng tỉ lệ thắng minigame +1% mỗi cấp", 10),
            "streak_hype": ("🎮 Hưng Phấn Chuỗi Thắng", "Thắng liên tiếp → thưởng thêm 200 xu", 3)
        }
    },
    "streamer": {
        "name": "Streamer tâm huyết",
        "description": "Tăng streak và tương tác cộng đồng!",
        "category": "entertainment",
        "emoji": "📹",
        "base_pay": 17000,
        "level_required": 30
    },

    # 🔧 Nhóm kỹ thuật
    "engineer": {
        "name": "Kỹ sư",
        "description": "Biến những dòng lệnh thành xu!",
        "category": "technical",
        "emoji": "💻",
        "base_pay": 15000,
        "level_required": 28,
        "skills": {
            "bug_convert": ("💻 Debug Đổi Cash", "Fix bug → nhận thêm job token mỗi 7 ngày", 1),
            "code_echo": ("💻 Code Echo", "Tăng `!work` reward thêm 100 nếu gõ code hôm đó", 3)
        }
    },
    "mechanic": {
        "name": "Thợ máy",
        "description": "Vặn ngược bug bằng cờ lê emoji!",
        "category": "technical",
        "emoji": "🔧",
        "base_pay": 8000,
        "level_required": 22
    },
    "data_analyst": {
        "name": "Chuyên viên phân tích dữ liệu",
        "description": "Phân tích số liệu của hệ thống để mở insight chưa ai nhìn thấy.",
        "category": "technical",
        "emoji": "📊",
        "base_pay": 20000,
        "level_required": 35
    },
    "network_admin": {
        "name": "Quản trị mạng",
        "description": "Giữ cho bot không lag và dữ liệu không đứt đoạn — sống trong tầng backend.",
        "category": "technical",
        "emoji": "🌐",
        "base_pay": 21500,
        "level_required": 38
    },
    #  Nhóm quản lý

        "project_manager": {
        "name": "Quản lý dự án",
        "description": "Gắn task, chia deadline, cố thuyết phục bot rằng 'feature sẽ ra đúng hẹn'.",
        "category": "management",
        "emoji": "🗂️",
        "base_pay": 125000,
        "level_required": 45
    },

    "product_owner": {
        "name": "Chủ nhiệm sản phẩm",
        "description": "Quản lý tính năng như sở hữu meta — phản hồi lệnh chưa ai viết.",
        "category": "management",
        "emoji": "🛠️",
        "base_pay": 150000,
        "level_required": 50
    },

    # 📚 Nhóm học giả
    "quiz_master": {
        "name": "Quái vật trivia",
        "description": "Thông thạo tất cả quiz khó!",
        "category": "scholar",
        "emoji": "📚",
        "base_pay": 13000,
        "level_required": 27,
        "skills": {
            "trivia_insight": ("📚 Kiến Thức Sâu", "Gạch 1 lựa chọn sai trong quiz", 1),
            "answer_speed": ("📚 Trả Lời Nhanh", "Tăng thời gian quiz +5s mỗi cấp", 2)
        }
    },
    "teacher": {
        "name": "Giáo viên tận tụy",
        "description": "Dạy cộng đồng bằng emoji và quote!",
        "category": "scholar",
        "emoji": "🧑‍🏫",
        "base_pay": 10000,
        "level_required": 25,
        "skills": {
            "teach_boost": ("🧑‍🏫 Truyền Dạy Cảm Hứng", "Gửi quote → nhận thêm token", 1),
            "quiz_push": ("🧑‍🏫 Thúc Đẩy Kiến Thức", "Tăng reward quiz người khác", 3)
        }
    },

    # 💰 Nhóm thương mại
    "merchant": {
        "name": "Thương nhân sành sỏi",
        "description": "Lời hay lỗ tùy vào giá hôm nay!",
        "category": "economy",
        "emoji": "💼",
        "base_pay": 11000,
        "level_required": 26,
        "skills": {
            "price_check": ("💼 Nhìn Giá Chuẩn", "Xem dự báo giá item trước khi bán", 3),
            "bulk_trade": ("💼 Buôn Sỉ Thường Xuyên", "Bán 10 item cùng lúc", 1)
        }
    },
    "banker": {
        "name": "Người gác kho coin",
        "description": "Leaderboard là sân nhà!",
        "category": "economy",
        "emoji": "🏦",
        "base_pay": 75000,
        "level_required": 35
    },

        "economist": {
        "name": "Nhà kinh tế học",
        "description": "Phân tích xu hệ thống, dự đoán giá tăng… trong một nền kinh tế không ai điều tiết.",
        "category": "economy",
        "emoji": "💹",
        "base_pay": 125000,
        "level_required": 45
    },

    "financial_advisor": {
        "name": "Cố vấn tài chính",
        "description": "Gợi chiến lược sử dụng coin — từ chi tiêu tiết kiệm tới 'mua vibe sống ngoài logic'.",
        "category": "economy",
        "emoji": "🏦",
        "base_pay": 175000,
        "level_required": 55
    }

}