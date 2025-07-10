from shared.data.achievements import ACH_LIST

class AchievementRegistry:
    def __init__(self):
        # dict: command_name -> set of achievement keys
        self.mapping = {}
        self.valid_keys = {k for k, *_ in ACH_LIST}

    def register(self, command: str, *keys):
        valid = [k for k in keys if k in self.valid_keys]
        invalid = [k for k in keys if k not in self.valid_keys]

        if invalid:
            print(f"[⚠️ Warning] Ignored invalid achievements: {invalid}")

        self.mapping.setdefault(command, set()).update(valid)

    def get(self, command: str):
        return list(self.mapping.get(command, []))

# 📦 Toàn bộ registry
ach_triggers = AchievementRegistry()

# Economy
ach_triggers.register("beg", "beg")
ach_triggers.register("daily", "daily", "daily3", "daily7", "daily14", "daily365", "daily1000")
ach_triggers.register("repay", "first_repay")
ach_triggers.register("give", "first_give")
ach_triggers.register("pray", "pray", "praybless")
ach_triggers.register("work", "first_work", "overtime1", "dedicated_worker", "job_token_master")
ach_triggers.register("crime", "crime")
ach_triggers.register("steal", "steal", "steal10", "lose5steals")
ach_triggers.register("profile", "profile_viewer")

# Shop & Item
ach_triggers.register("buy", "buy")
ach_triggers.register("useitem", "use_xp_juice", "used_energy_drink", "birthday_mythical")

# GiftCode
ach_triggers.register("redeemcode", "giftcode1", "giftcode10")

# Quest
ach_triggers.register("complete", "quest_beginner", "quest_master")

# Minigame & Quiz
ach_triggers.register("guess", "play3", "play10", "win1", "win5")
ach_triggers.register("coinflip", "play3", "play10", "win1", "win5")
ach_triggers.register("oantutim", "play3", "play10", "win1", "win5")
ach_triggers.register("quiz", "quiz_normal", "quiz_hard", "quiz_extreme", "quiz_nightmare")
ach_triggers.register("speedrunquiz", "sq10")
ach_triggers.register("chaos", "chaos_winner")

# Social
ach_triggers.register("trust", "trust_given")
ach_triggers.register("thank", "thanked_once")
ach_triggers.register("shoutout", "social_star")
ach_triggers.register("chat", "chat10")

# Hidden
ach_triggers.register("mirror", "secretcmd1")
ach_triggers.register("meow", "secretcmd1")
ach_triggers.register("echo", "secretcmd1")
ach_triggers.register("unlock", "hidden_trigger")

# Level / XP / Misc
ach_triggers.register("adminboost", "adminboost", "adminreset")
ach_triggers.register("levelup", "lv5", "lv10", "lv25", "lv50")
ach_triggers.register("voice", "voice1h")

# Leaderboard
ach_triggers.register("weeklyboard", "leader_level", "leader_cash")