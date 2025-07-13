# data/achievements.py

ACH_LIST = [
    # Economy
    ("beg",         "👶 Lần đầu xin ăn",        "Dùng !beg lần đầu",                       False),
    ("daily",        "📆 Ngày đầu tiên",         "Dùng !daily lần đầu",                     False),
    ("first_repay",   "💳 Lần đầu trả nợ",       "Hoàn thành lệnh !repay lần đầu", False),
    ("first_give",    "💸 Lần đầu tặng tiền",        "Hoàn thành lệnh !give lần đầu",  False),
    ("daily3",            "🎁 3 ngày chăm chỉ",       "Nhận 3 ngày liên tục",                    False),
    ("daily7",            "🔥 Tuần vững vàng",         "Nhận 7 ngày liên tục",                    False),
    ("daily14",           "🗓️ 14 ngày liên hoàn",     "Nhận 14 ngày liên tục",                   False),
    ("daily365",          "📆 Cả năm ròng rã",         "Nhận 365 ngày liên tục",                  False),
    ("daily1000",         "🌟 Millennium",            "Nhận 1000 ngày liên tục",                 False),
    ("profile_viewer", "📋 Profile Viewer", "Xem hồ sơ người chơi lần đầu", False),

    ("pray",        "🙏 Lần đầu cầu nguyện",     "Dùng !pray lần đầu",                      False),
    ("praybless",         "🌟 Phép màu mỉm cười",      "Nhận reward hiếm trong !pray",            True),
    ("funni",           "🔥 Tôi nắm giữ 1 tỷ số trong đầu", "Đoán trúng số trong funni guess",    True),

    ("first_work",        "👷 Lần đầu làm việc",      "Dùng !work lần đầu",                      False),
    ("overtime1",         "⏰ Tăng ca lần đầu",        "Nhận x3 bonus trong !work",               False),
    ("dedicated_worker",  "💼 Chuyên cần",            "10 lần !work có bonus",                   False),
    ("job_token_master", "💼 Token Collector", "Sở hữu 10 Job Token", False),

    ("crime",            "🚔 Tội phạm mới",          "Thành công !crime lần đầu",               False),
    ("steal",            "🦹 Vụ trộm đầu đời",       "Thành công !steal lần đầu",               False),
    ("steal10",           "💼 Bậc thầy móc túi",      "Thực hiện 10 lần !steal thành công",      False),
    ("lose5steals",       "🪤 Bị bắt 5 lần",         "Thất bại 5 lần !steal",                   True),

    # Shop & Item
    ("buy",        "🛍️ Shop Master",         "Mua lần đầu từ shop",                      False),
    ("use_xp_juice",      "⚡ XP Enthusiast",         "Dùng 10 XP Juice",                        False),
    ("used_energy_drink", "⚡ Energized",            "Dùng 5 Energy Drink",                     False),
    ("birthday_mythical", "🎂 Sinh nhật thần thánh",   "Dùng Anniversary Token đúng 4/4",         True),

    # GiftCode
    ("giftcode1",         "🎁 Gift Hunter",          "Nhập 1 giftcode",                        False),
    ("giftcode10",        "🎉 Giftcode King",        "Nhập 10 giftcode",                       False),

    # Quests
    ("quest_beginner",    "🗡️ Quest Novice",        "Hoàn thành quest đầu tiên",                 False),
    ("quest_master",      "🛡️ Quest Master",        "Hoàn thành 10 quest",                      False),

    # Minigame
    ("play3",             "🎮 Game Starter",        "Tham gia 3 minigame",                      False),
    ("play10",            "👾 Addicted",            "Tham gia 10 minigame",                     False),
    ("win1",              "🏆 First Win",           "Thắng minigame lần đầu",                   False),
    ("win5",              "🥇 Champion",            "Thắng 5 minigame",                         False),
    ("quiz_normal",       "📊 Quiz Normal",         "Hoàn thành 10 quiz Normal",                False),
    ("quiz_hard",         "🔥 Quiz Hard",           "Hoàn thành 10 quiz Hard",                  False),
    ("quiz_extreme",      "💀 Quiz Extreme",        "Hoàn thành 5 quiz Extreme",                True),
    ("quiz_nightmare",    "👾 Quiz Nightmare",      "Hoàn thành 3 quiz Nightmare",              True),
    ("sq10",              "⏱️ Speedrunner",         "Hoàn thành 10 round SpeedrunQuiz",         False),
    ("uno_reverse", "🔄 UNO'd", "Bot đã đoán trúng suy nghĩ của bạn. Reverse đúng chất!", False),
    ("oneshot_hit", "🎯 Trúng Phát Ăn Ngay", "Bạn đã đoán đúng chỉ trong một lần duy nhất.", False),
    ("burncoin_maniac", "🔥 Người Đốt Xóm", "Đã đốt hơn 1 triệu xu. Không tiếc – không nhìn lại.", False),

    ("chaos_winner",      "💥 Chaos Champion",      "Thắng 5 lượt Chaos Game",                  False),

    # Social
    ("chat10",            "💬 Chatter",             "Gửi 10 tin nhắn",                          False),
    ("trust_given",       "🤝 Trust Giver",         "Dùng !trust cho 5 người",                  False),
    ("thanked_once",      "💛 First Thank",         "Nhận 1 !thank",                            False),
    ("social_star",       "🌟 Social Star",         "Gửi shoutout lần đầu",                     False),
    ("mirror", "🪞 Gương", "Không có mô tả gì, chỉ là chính bạn.", False),

    # Hidden
    ("secretcmd1",        "🔒 Secret Finder",       "Dùng 1 lệnh ẩn",                           True),
    ("hidden_trigger",    "🔮 Seeker",              "Unlock lệnh ẩn",                           True),
    ("hole", "🕳️ Tiếng Vọng Từ Hư Vô", "Spam emoji này sau 5 lệnh khác nhau. Bạn đang sống lệch chiều.", True),
    ("fish", "🐟 Cá", "Cá", True),
    ("b_box", "🧃 Hộp Ý thức", "Không ai cần biết nó để làm gì và cũng không ai muốn biết", True),
    ("mirrorloop", "🪞 Vòng Lặp Tâm Thức", "Bạn đã soi gương quá nhiều lần mà không biết mình là ai.", True),

    # Level & XP
    ("lv5",               "📈 Level 5",             "Đạt cấp độ 5",                             False),
    ("lv10",              "🌟 Level 10",            "Đạt cấp độ 10",                            False),
    ("lv25",              "💡 Level 25",            "Đạt cấp độ 25",                            False),
    ("lv50",              "🧠 Level 50",            "Đạt cấp độ 50",                            False),
    ("voice1h",           "🎤 Voice 1h",            "Tổng voice ≥1h",                           False),

    # Admin
    ("adminboost",        "🌟 The Protagonist",         "Được tặng coin bởi admin",                 True),
    ("adminreset",        "🔄 The Villain Arc",         "Bị reset bởi admin",                       True),

    # Leaderboard
    ("leader_level",      "🏅 Top Level",           "Top 5 Level",                              False),
    ("leader_cash",       "💎 Cash King",           "Top 5 Wallet",                             False),

    # Mastery Job Achievements
    ("master_cn", "🧱 Bậc Thầy Công Nhân", "Hoàn thành thành thạo nghề Công nhân", False),
    ("master_cn_manager", "🏭 Bậc Thầy Quản Lý Công Nhân", "Hoàn thành thành thạo nghề Quản lý công nhân", False),
    ("master_os", "🧑‍💻 Bậc Thầy Nhân Viên Văn Phòng", "Hoàn thành thành thạo nghề Nhân viên văn phòng", False),
    ("master_os_manager", "📈 Bậc Thầy Quản Lý Văn Phòng", "Hoàn thành thành thạo nghề Quản lý văn phòng", False),
    ("master_cc", "🎨 Bậc Thầy Nhà Sáng Tạo Nội Dung", "Hoàn thành thành thạo nghề Nhà sáng tạo nội dung", False),
    ("master_cd", "🧑‍✈️ Bậc Thầy Giám Đốc Công Ty", "Hoàn thành thành thạo nghề Giám đốc công ty", False),
    ("master_ux_designer", "🎨 Bậc Thầy Thiết Kế Trải Nghiệm", "Hoàn thành thành thạo nghề Thiết kế trải nghiệm", False),
    ("master_content_writer", "📝 Bậc Thầy Biên Tập Nội Dung", "Hoàn thành thành thạo nghề Biên tập nội dung", False),
    ("master_gamer", "🎮 Bậc Thầy Game Thủ Chuyên Nghiệp", "Hoàn thành thành thạo nghề Game thủ chuyên nghiệp", False),
    ("master_streamer", "📹 Bậc Thầy Streamer Tâm Huyết", "Hoàn thành thành thạo nghề Streamer tâm huyết", False),
    ("master_engineer", "💻 Bậc Thầy Kỹ Sư", "Hoàn thành thành thạo nghề Kỹ sư", False),
    ("master_mechanic", "🔧 Bậc Thầy Thợ Máy", "Hoàn thành thành thạo nghề Thợ máy", False),
    ("master_data_analyst", "📊 Bậc Thầy Chuyên Viên Phân Tích Dữ Liệu", "Hoàn thành thành thạo nghề Chuyên viên phân tích dữ liệu", False),
    ("master_network_admin", "🌐 Bậc Thầy Quản Trị Mạng", "Hoàn thành thành thạo nghề Quản trị mạng", False),
    ("master_project_manager", "🗂️ Bậc Thầy Quản Lý Dự Án", "Hoàn thành thành thạo nghề Quản lý dự án", False),
    ("master_product_owner", "🛠️ Bậc Thầy Chủ Nhiệm Sản Phẩm", "Hoàn thành thành thạo nghề Chủ nhiệm sản phẩm", False)
]
