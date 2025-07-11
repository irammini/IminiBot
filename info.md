Thông tin chi tiết về IminiBot (v.pre-3.8):
Về thông tin tổng quan:
- IminiBot sử dụng thư viện nextcord hỗ trợ python, sử dụng database PostgreSQL SQLAlchemy với ORM mạnh phù hợp với bot mang nhiều tính năng cả hiện tại và tương lai như IminiBot. IminiBot chỉ sử dụng prefix truyền thống, không hỗ trợ slash command.
- IminiBot được phát triển chính thức vào ngày 4 tháng 4 năm 2024, với phiên bản đầu tiên được ra mắt vào ngày 18 tháng 4 năm 2024 (1.0). Thời điểm đó bot còn sử dụng SQLite và đã được thay đổi như hiện tại.
- IminiBot được tạo với mục đích giải trí, do đúng 1 developer xử lý toàn bộ mọi thứ. IminiBot được tạo ra vì đam mê, không vì kinh doanh hay danh tiếng.
- IminiBot ở phiên bản mới nhất hiện tại có 17 cogs (4 trong đó vẫn đang được phát triển), 7 file data chứa dữ liệu phù hợp cho các cog. 15 models cung cấp database và 6 utils hỗ trợ cho mục đích cụ thể.
Về các câu lệnh/tính năng
- IminiBot có rất nhiều lệnh khác nhau, hầu hết chúng đều được liệt kê trong !bothelp
+ Tính năng/lệnh của cog economy:
Note:Đơn vị tiền tệ của IminiBot là IminiCash, chúng có thể được xem trong !profile.
!daily: Nhận thưởng hằng ngày và +1 streak (+2 nếu đã sử dụng item Streak Charge)
!beg: Ăn xin với xác xuất nhận được ít tiền.
!crime: Phạm tội với xác xuất thấp nhận được nhiều tiền, bị bắt và trừ tiền nếu không thành công. Người chơi sẽ bị "nợ" nếu số tiền không đủ để trả.
!repay: Trả nợ một phần hoặc toàn bộ nợ.
!deposit: Chuyển tiền vào ngân hàng (giới hạn 1 tỷ IminiCash, có thể xem chi tiết trong !profile)
!withdraw: Rút tiền từ ngân hàng
!steal: Trộm người khác (cả hai cần đạt level 15)
!give: Tặng người khác tiền
!pray: Cầu nguyện với xác xuất cực nhỏ nhận được 1-5 triệu IminiCash, tích lũy pray point tăng may mắn cho !pray (lượng rất nhỏ). Ghi chú khác:Nếu pray point gần 50000 thì xác xuất nhận tiền là 100%.
+ Tính năng/lệnh của cog levelsystem:
Note: Cog này chủ yếu là hệ thống level của IminiBot, chỉ có 2 lệnh.
!setflex: Sử dụng badge (achievement) để hiển thị trong profile. Badge càng hiếm thì độ "flex" càng cao.
!unsetflex: Như tên.
+ Tính năng/lệnh của cog achievement:
Note: Cog này chủ yếu seed achievement có trong data/achievements.py, chỉ có 2 lệnh.
!achievements: Hiển thị toàn bộ achievement đã sỡ hữu.
!achievementkeys: Hiển thị tất cả badge public (không bị ẩn)
+ Tính năng/lệnh của cog minigame:
Note: Lệnh !quiz vẫn còn đang phát triển, không phải cả cái cog.
!guess: Đoán từ 1-10, trúng thì nhận thưởng.
!guess "Funni mode": Xác xuất xuất hiện là 0.1% mỗi lần dùng !guess, đoán từ 1-1 tỷ, trúng bằng cách nào đó thì nhận 1 triệu tỷ IminiCash. Tính năng này thêm vào cho vui là chính, ai mà trúng thì phá vỡ cả IminiCash price.
!inverseguess: Thay vì tự đoán thì bạn đưa số rồi bot đoán (từ 1-100), trúng thì nhận thưởng lớn hơn đáng kể.
!oneshot: Minigame chơi một lần duy nhất, vẫn là đoán từ 1-100. Trúng thì nhận 1 triệu IminiCash và badge.
!spill: Làm "đổ" thứ gì đó ngẫu nhiên. Có thể nhận item hoặc chỉ bị troll.
!quiz: Có menu chọn độ khó khi sử dụng, tính năng nâng cấp độ khó vẫn còn đang phát triển. Hiện tại easy mode là bản chơi được.
!speedrunquiz: Chơi easy mode liên tục với thời gian trả lời ngắn hơn.
!coinflip: Lật xu heads hoặc tails.
!oantutim: Oẳn tù tì kéo búa hoặc bao.
!burncoin: Đốt tiền vì flex hoặc vì tức giận, đốt trên 1 triệu nhận badge.
+ Tính năng/lệnh của cog quest:
Note: Do DAILY_POOL chưa đủ quest để roll nên lệnh !quest hiện tại không dùng được, không phải lỗi quá nặng nề.
!quest: Hiển thị quest daily/weekly thông qua reaction.
!complete: Hoàn thành quest nếu đủ điều kiện.
