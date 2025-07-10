import nextcord
import random

# Màu sắc theo rarity
RARITY_COLORS = {
    "Common":    nextcord.Color.greyple(),
    "Uncommon":  nextcord.Color.green(),
    "Rare":      nextcord.Color.blue(),
    "Epic":      nextcord.Color.purple(),
    "Legendary": nextcord.Color.gold(),
    "Mythical":  nextcord.Color.red(),
}

# Các món treasure seed cũ trong shop
TREASURE_ITEMS = [
    ("dino_bone",  "Xương khủng long",   "Legendary", 50000),
    ("deep_key",   "Chìa khóa biển sâu", "Mythical",  0),
    ("shark_head", "Đầu cá mập",         "Epic", 5000),
    ("whale_tail", "Đuôi cá voi",         "Epic", 5000),
    ("dog_shield", "Dog Shield",          "Rare",      2000),
]

# Danh sách item chính
# Format: (id, display_name, description, rarity, category, [price])
ITEMS = [
    # 🎉 Sự kiện đặc biệt
    {
        "key": "anniversary_token",
        "name": "Anniversary Token",
        "price": 0,
        "emoji": "🎂",
        "limit": 1
    },

    # ⚡ Buff & Economy
    {
        "key": "energy_drink",
        "name": "Nước tăng lực",
        "price": 5000,
        "emoji": "🥤",
        "limit": 3
    },
    {
        "key": "streak_charge",
        "name": "Streak Charge",
        "price": 10000,
        "emoji": "⚡",
        "limit": 2
    },
    {
        "key": "iminicash_bag",
        "name": "Iminicash Bag",
        "price": 500,
        "emoji": "💰",
        "limit": 5
    },
    {
        "key": "xp_juice",
        "name": "XP Juice",
        "price": 4000,
        "emoji": "🧪",
        "limit": 3
    },
    {
        "key": "holy_charm",
        "name": "Holy Charm",
        "price": 15000,
        "emoji": "🕯️",
        "limit": 1
    },

    # 🎨 Profile trang trí
    {
        "key": "profile_ribbon",
        "name": "Profile Ribbon",
        "price": 750,
        "emoji": "🎀",
        "limit": 1
    },
    {
        "key": "profile_emoji",
        "name": "Profile Emoji",
        "price": 850,
        "emoji": "😎",
        "limit": 1
    },
    {
        "key": "color_accent",
        "name": "Color Accent",
        "price": 1800,
        "emoji": "🎨",
        "limit": 1
    },
        {
        "key": "title_customizer",
        "name": "Custom Title",
        "price": 1200,
        "emoji": "🏆",
        "limit": 1,
        "category": "style"
    },
    {
        "key": "profile_theme",
        "name": "Profile Theme",
        "price": 1600,
        "emoji": "🎭",
        "limit": 1,
        "category": "style"
    },
    {
        "key": "frame_override",
        "name": "Frame Override",
        "price": 1900,
        "emoji": "🧊",
        "limit": 1,
        "category": "style"
    },

    # 🤝 Social & tiện ích
    {
        "key": "retry_token",
        "name": "Retry Token",
        "price": 100,
        "emoji": "🔁",
        "limit": 2
    },
    {
        "key": "thank_token",
        "name": "Thank Token",
        "price": 1000,
        "emoji": "💛",
        "limit": 1
    },
    {
        "key": "shop_voucher",
        "name": "Shop Voucher",
        "price": 0,
        "emoji": "🎫",
        "limit": 1
    },

    # ⏭️ Nhiệm vụ & quiz
    {
        "key": "skip_quest",
        "name": "Skip Quest",
        "price": 25000,
        "emoji": "⏭️",
        "limit": 1
    },

    # 🍀 Crate ngẫu nhiên
    {
        "key": "crate",
        "name": "Crate",
        "price": 3500,
        "emoji": "📦",
        "limit": 3
    },
    {
        "key": "luck_crate",
        "name": "Luck Crate",
        "price": 8000,
        "emoji": "🍀",
        "limit": 2
    },
    {
        "key": "fish_crate",
        "name": "Fish Crate",
        "price": 2000,
        "emoji": "🐟",
        "limit": 2
    },
    {
        "key": "treasure_chest",
        "name": "Hòm kho báu",
        "price": 0,
        "emoji": "📦",
        "limit": 2
    }
]

# KHÔNG Bổ sung lại các treasure items cũ vào ITEM_LIST
def get_random_treasure():
    return random.choice(TREASURE_ITEMS)