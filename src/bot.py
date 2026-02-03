import os
import random
from datetime import datetime, timedelta, time as dtime
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from src.core import midnight_range_for_yesterday
from src.database import Database
from src.config_loader import Config

load_dotenv()

import logging

# logger setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("cookie_v2bot")
# suppress HTTP/urllib3 logs
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


class CookieBot:

    def __init__(
        self,
        token: str = None,
        config_path: str | None = None,
        db_path: str | None = None,
    ):
        token = token or os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError("BOT_TOKEN is required in environment or passed")
        self.cfg = Config(config_path or "config/config.toml")
        self.achievements = Config("config/achievements.toml")
        self.badges = Config("config/badges.toml")
        self.cards = Config("config/cards.toml")
        self.levels = Config("config/level.toml")
        self.db = Database(db_path or "data/chat.db")
        self.app = ApplicationBuilder().token(token).build()
        self.app.add_handler(
            MessageHandler(filters.ALL & ~filters.COMMAND, self.on_message)
        )
        # 命令处理
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("ping", self.cmd_ping))
        self.app.add_handler(CommandHandler("achievements", self.cmd_achievements))
        self.app.add_handler(CommandHandler("badges", self.cmd_badges))
        self.app.add_handler(CommandHandler("cards", self.cmd_cards))
        self.app.add_handler(CommandHandler("myachievements", self.cmd_my_achievements))
        self.app.add_handler(CommandHandler("mybadges", self.cmd_my_badges))
        self.app.add_handler(CommandHandler("mycards", self.cmd_my_cards))
        self.app.add_handler(CommandHandler("buycard", self.cmd_buy_card))
        self.app.add_handler(CommandHandler("myinfo", self.cmd_myinfo))
        self.app.add_handler(CommandHandler("leaderboard", self.cmd_leaderboard))
        self.app.add_handler(
            CommandHandler("yesterday_report", self.cmd_yesterday_report)
        )

        self.app.job_queue.run_daily(
            self.daily_job, time=dtime(hour=0, minute=0, second=5)
        )
        logger.info("CookieBot 初始化成功!")

    async def start(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        await self.app.stop()
        await self.app.shutdown()

    def _msg_type(self, message) -> str:
        if message.photo:
            return "photo"
        if message.sticker:
            return "sticker"
        if message.voice:
            return "voice"
        if message.text:
            return "text"
        return "other"

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        m = update.effective_message
        if not m or not update.effective_user:
            return
        user = update.effective_user
        chat = update.effective_chat
        msg_type = self._msg_type(m)
        ts = int(m.date.timestamp())

        logger.debug(
            "收到消息: user=%s chat=%s type=%s ts=%s",
            getattr(user, "id", None),
            getattr(chat, "id", None),
            msg_type,
            ts,
        )

        # ensure user record
        try:
            self.db.upsert_user(user.id, user.username, user.first_name, user.last_name)
            logger.debug("记录用户 %s (%s)", user.id, user.username)
        except Exception:
            logger.exception("无法记录用户 %s", getattr(user, "id", None))

        # ensure chat record (store title/name when available)
        try:
            chat_title = (
                getattr(chat, "title", None) or getattr(chat, "name", None) or None
            )
            if chat_title:
                self.db.upsert_chat(chat.id, chat_title)
                logger.debug(
                    "记录群聊 %s title=%s", getattr(chat, "id", None), chat_title
                )
        except Exception:
            logger.exception("无法记录群聊 %s", getattr(chat, "id", None))

        await self._add_exp(user, chat, msg_type, ts, update, context)

        # optional playful reply (喵喵语) with low probability
        if random.random() < 0.02:
            phrase = random.choice(
                self.cfg.get("phrases", "meows", default=["喵~", "喵喵～", "喵呜~"])
            )
            await m.reply_text(phrase)
            logger.debug("已用俏皮短语回复用户 %s", getattr(user, "id", None))

        await self._unlock_achievement(user, chat, msg_type, ts, m)

        await self._unlock_badge(user, chat, m, ts)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /start", getattr(user, "id", None))
        activity_name = self.cfg.get("activity", "name", default="喵喵成长日记")
        activity_desc = self.cfg.get("activity", "description", default="")

        msg = f"""🎉 <b>欢迎来到 {activity_name}</b> 喵!
<b><i>{activity_desc}</i></b>

📝 <b>快速开始：</b>
• 在群组中发送消息，赚取经验值
• 使用 /myinfo 查看个人成长情况
• 使用 /leaderboard 查看排行榜

💡 <b>有问题？</b>
输入 /help 查看完整命令列表
"""
        await update.effective_message.reply_html(msg)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /help", getattr(user, "id", None))
        msg = """🐱 <b>喵喵成长日记 - 命令帮助</b>

<b>📊 个人信息</b>
/myinfo - 查看你的个人信息和成长数据
  • 昨日消息统计
  • 累计消息统计
  • 总经验值

/myachievements - 查看你的成就和奖励
/mybadges - 查看你的徽章
/mycards - 查看你的卡片

<b>🏆 排行榜</b>
/leaderboard - 查看昨日排行榜（top 10）
/leaderboard all - 查看全部时间排行榜

<b>📈 统计报告</b>
/yesterday_report - 查看昨日统计报告
  • 昨日总消息数
  • 活跃用户排名

<b>👀 所有内容</b>
/achievements - 查看所有成就
/badges - 查看所有徽章
/cards - 查看所有卡片

<b>🏬 购买</b>
/buycard (id) - 购买一个卡片

<b>🔧 系统命令</b>
/start - 显示欢迎信息
/help - 显示此帮助信息
/ping - 测试机器人连接状态

<b>✨ 消息获得经验：</b>
📝 文本消息: 1 点
🖼️ 图片: 3 点
🎵 语音: 3 点
🎨 贴纸: 2 点

⚠️ 每日经验有上限，珍惜每条消息！

有任何问题？联系群组管理员 👨‍💼
"""
        await update.effective_message.reply_html(msg)

    async def cmd_ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /ping 命令 - 测试连接"""
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /ping", getattr(user, "id", None))
        msg = f"🏓 <b>Pong!</b>"
        await update.effective_message.reply_html(msg)

    async def cmd_myinfo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        logger.info("用户 %s 执行了命令 /myinfo", getattr(user, "id", None))
        if not user:
            return
        # yesterday and total
        y_start, y_end = midnight_range_for_yesterday()
        yesterday = self.db.get_user_counts(user.id, start_ts=y_start, end_ts=y_end)
        total = self.db.get_user_counts(user.id, start_ts=None, end_ts=None)
        total_user = self.db.conn.execute(
            "SELECT total_exp FROM users WHERE user_id = ?", (user.id,)
        ).fetchone()
        exp_total = total_user[0] if total_user else 0

        # 获取用户等级
        user_level = self.db.get_user_level(user.id)

        # 计算下一等级需要的经验值
        next_level_need = self._get_next_level_exp_needed(user_level)
        if next_level_need == 0:
            # 已经是最高等级
            next_level_need = exp_total

        # 计算今天获取的经验值
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_ts = int(today_start.timestamp())

        # 获取今天的消息统计
        today_counts = self.db.get_user_counts(user.id, start_ts=today_ts, end_ts=None)

        # 计算今天获得的经验值
        points_map = self.cfg.get("experience", "points", default={})
        today_exp = 0
        for t, cnt in today_counts.items():
            if t == "total":
                continue
            p = int(points_map.get(t, points_map.get("text", default=1)))
            today_exp += p * cnt

        # 构建美观的消息
        txt = f"""
🎯 <b>喵喵个人信息</b>

👤 <b>用户信息</b>
名字: {user.full_name}
ID: <code>{user.id}</code>

⭐ <b>总经验值: {exp_total}/{next_level_need}</b>
🔥 <b>今日经验: {today_exp}</b>
🏆 <b>等级: {user_level}</b>

📊 <b>昨日统计</b>
"""
        for k, v in yesterday.items():
            if k == "total":
                txt += f"总计: <code>{v}</code>\n"
            else:
                emoji_map = {
                    "text": "📝",
                    "photo": "🖼️",
                    "voice": "🎵",
                    "sticker": "🎨",
                    "other": "📦",
                }
                emoji = emoji_map.get(k, default="📌")
                txt += f"{emoji} {k}: <code>{v}</code>\n"

        txt += "\n📈 <b>累计统计</b>\n"
        for k, v in total.items():
            if k == "total":
                txt += f"总计: <code>{v}</code>\n"
            else:
                emoji_map = {
                    "text": "📝",
                    "photo": "🖼️",
                    "voice": "🎵",
                    "sticker": "🎨",
                    "other": "📦",
                }
                emoji = emoji_map.get(k, default="📌")
                txt += f"{emoji} {k}: <code>{v}</code>\n"

        txt += """

<b>更多内容:</b>
成就: /myachievements
徽章: /mybadges
卡片: /mycards
"""

        txt += f"\n✨ 继续加油！每天都有新惊喜！"

        await update.effective_message.reply_html(txt)

    async def cmd_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args or []
        mode = args[0] if args else "daily"
        user = update.effective_user
        logger.info(
            "用户 %s 执行了命令 /leaderboard (mode=%s)",
            getattr(user, "id", None),
            mode,
        )
        chat = update.effective_chat
        if mode == "all":
            rows = self.db.get_leaderboard_with_names(
                chat.id, start_ts=None, end_ts=None, limit=10
            )
            title = "🏆 全部排行榜"
            emoji = "🎯"
        else:
            y_start, y_end = midnight_range_for_yesterday()
            rows = self.db.get_leaderboard_with_names(
                chat.id, start_ts=y_start, end_ts=y_end, limit=10
            )
            title = "🏆 昨日排行榜"
            emoji = "🔥"

        def format_name(r):
            first = r["first_name"] or ""
            last = r["last_name"] or ""
            username = r["username"]
            name_parts = [p for p in [first, last] if p]
            name = " ".join(name_parts) if name_parts else f"ID:{r['user_id']}"
            if r["username"]:
                # tg://user?id={r["user_id"]}
                if username == getattr(user, "username", None):
                    return f'<a href="t.me/{username}"><b>{name}</b></a>'
                else:
                    return f'<a href="t.me/{username}">{name}</a>'
            return name

        if not rows:
            msg = "📉 暂无排行榜数据"
        else:
            # 奖牌emoji
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for i, r in enumerate(rows):
                medal = medals[i] if i < 3 else f"{i+1}️⃣"
                lines.append(
                    f"{medal} {format_name(r)} — <code>{r['cnt']}</code> 条消息"
                )

            msg = f"<b>{title}</b>\n\n" + "\n".join(lines)

        await update.effective_message.reply_html(
            msg,
            disable_web_page_preview=True,
        )

    async def cmd_yesterday_report(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        # manual trigger: report yesterday stats for this chat
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /yesterday_report", getattr(user, "id", None))
        chat = update.effective_chat
        y_start, y_end = midnight_range_for_yesterday()
        total = self.db.get_total_messages(start_ts=y_start, end_ts=y_end)
        rows = self.db.get_leaderboard_with_names(
            chat.id, start_ts=y_start, end_ts=y_end, limit=10
        )

        def format_name(r):
            first = r["first_name"] or ""
            last = r["last_name"] or ""
            username = r["username"]
            name_parts = [p for p in [first, last] if p]
            name = " ".join(name_parts) if name_parts else f"ID:{r['user_id']}"
            if username:
                return f"{name} (@{username})"
            return name

        if not rows:
            msg = "📰 <b>喵喵昨日日报</b>\n\n总消息数: <code>0</code>\n\n😴 昨日无活跃用户，看来大家都休息啦~"
        else:
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for i, r in enumerate(rows):
                medal = medals[i] if i < 3 else f"{i+1}️⃣"
                lines.append(
                    f"{medal} {format_name(r)} — <code>{r['cnt']}</code> 条消息"
                )

            msg = f"""📰 <b>喵喵昨日日报</b>

📊 <b>昨日总消息数</b>: <code>{total}</code>

🏆 <b>活跃用户排名</b>:
""" + "\n".join(
                lines
            )

        await update.effective_message.reply_html(msg)

    async def daily_job(self, context: ContextTypes.DEFAULT_TYPE):
        # run at 00:00, report yesterday
        y_start, y_end = midnight_range_for_yesterday()
        total = self.db.get_total_messages(start_ts=y_start, end_ts=y_end)
        chats = self.db.get_known_chats()

        def format_name(r):
            first = r["first_name"] or ""
            last = r["last_name"] or ""
            username = r["username"]
            name_parts = [p for p in [first, last] if p]
            name = " ".join(name_parts) if name_parts else f"ID:{r['user_id']}"
            if username:
                return f"{name} (@{username})"
            return name

        for cid in chats:
            rows = self.db.get_leaderboard_with_names(
                cid, start_ts=y_start, end_ts=y_end, limit=10
            )

            if not rows:
                txt = """🌙 <b>喵喵晨间日报</b>

📊 昨日总消息数: <code>0</code>

😴 昨日无活跃用户，看来大家都休息啦~

✨ 今天继续加油！"""
            else:
                medals = ["🥇", "🥈", "🥉"]
                lines = []
                for i, r in enumerate(rows):
                    medal = medals[i] if i < 3 else f"{i+1}️⃣"
                    lines.append(f"{medal} {format_name(r)} — <code>{r['cnt']}</code>")

                txt = (
                    f"""🌙 <b>喵喵晨间日报</b>

📊 <b>昨日总消息数</b>: <code>{total}</code>

🏆 <b>活跃用户排名</b>:
"""
                    + "\n".join(lines)
                    + f"""

✨ 开启新的一天，继续成长吧！"""
                )

            try:
                await context.bot.send_message(cid, txt, parse_mode="HTML")
                logger.info("在 %s 中发送了报告", cid)
            except Exception:
                logger.exception("在 %s 中发送报告失败", cid)
                continue

    async def cmd_achievements(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /achievements", getattr(user, "id", None))

        # 获取所有成就介绍
        achievements: list = self.achievements.get("achievements")
        # 格式化成就介绍
        lines = []
        for a in achievements:
            lines.append(f"{a['emoji']} <b>{a['name']}</b> — {a['description']}")
        msg = f"📰 <b>喵喵成就介绍</b>\n\n" + "\n".join(lines)
        # 发送成就介绍
        await update.effective_message.reply_html(msg)

    async def cmd_my_achievements(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user = update.effective_user
        logger.info(
            "用户 %s 执行了命令 /myachievements",
            getattr(user, "id", None),
        )

        # 获取用户成就
        user_achievements: list = self.db.get_user_achievements(user.id)
        all_achievements: list = self.achievements.get("achievements")
        # 格式化成就介绍
        lines = []
        warnings = []
        for achievement in user_achievements:
            # 查找对应的完整成就信息
            achievement_info = next(
                (a for a in all_achievements if a["name"] == achievement["name"]),
                None,
            )
            if achievement_info:
                # 格式化时间
                ts = achievement.get("ts", default=0)
                time_str = (
                    datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    if ts
                    else "未知时间"
                )
                lines.append(
                    f"{achievement_info['emoji']} <b>{achievement_info['name']}</b> — "
                    f"解锁时间: {time_str}"
                )
            else:
                # 格式化时间
                ts = achievement.get("ts", default=0)
                time_str = (
                    datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    if ts
                    else "未知时间"
                )
                lines.append(f"<b>{achievement['name']}</b> — 解锁时间: {time_str}")
                warnings.append(f"成就 {achievement['name']}")

        if not lines:
            lines.append("你还没有解锁任何成就，继续努力吧！")

        msg = f"📰 <b>我的成就</b>\n\n" + "\n".join(lines)

        # 添加警告信息
        if warnings:
            msg += "\n\n⚠️ <b>警告：</b>"
            for warning in warnings:
                msg += f"{warning} 未找到\n"

        # 发送成就介绍
        await update.effective_message.reply_html(msg)

    async def cmd_badges(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /badges", getattr(user, "id", None))

        # 获取所有徽章介绍
        badges: list = self.badges.get("badges", default=[])
        # 格式化徽章介绍
        lines = []
        for b in badges:
            lines.append(f"{b['emoji']} <b>{b['name']}</b> — {b['description']}")
        msg = f"📰 <b>喵喵徽章介绍</b>\n\n" + "\n".join(lines)
        # 发送徽章介绍
        await update.effective_message.reply_html(msg)

    async def cmd_my_badges(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /mybadges", getattr(user, "id", None))

        # 获取用户徽章
        user_badges: list = self.db.get_user_badges(user.id)
        # 获取所有徽章
        all_badges: list = self.badges.get("badges", default=[])
        # 格式化徽章介绍
        lines = []
        warnings = []
        for badge_name in user_badges:
            # 查找对应的完整徽章信息
            badge_info = next((b for b in all_badges if b["name"] == badge_name), None)
            if badge_info:
                lines.append(f"{badge_info['emoji']} <b>{badge_info['name']}</b>")
            else:
                lines.append(f"<b>{badge_name}</b>")
                warnings.append(f"徽章 {badge_name}")

        if not lines:
            lines.append("你还没有获得任何徽章，继续努力吧！")

        msg = f"📰 <b>我的徽章</b>\n\n" + "\n".join(lines)

        # 添加警告信息
        if warnings:
            msg += "\n\n⚠️ <b>警告：</b>"
            for warning in warnings:
                msg += f"{warning} 未找到\n"

        # 发送徽章介绍
        await update.effective_message.reply_html(msg)

    async def cmd_cards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /cards", getattr(user, "id", None))

        # 获取所有卡片介绍
        cards: list = self.cards.get("cards", default=[])
        # 格式化卡片介绍
        lines = []
        for c in cards:
            point = c.get("point", default=0)
            lines.append(
                f"{c['emoji']} <b><code>{c['name']}</code></b> — "
                f"{c['description']} <i>(需要 {point} 经验值)</i>"
            )
        msg = f"📰 <b>喵喵卡片介绍</b>\n\n" + "\n".join(lines)
        msg += "\n\nℹ <b>提示:</b> 如果要使用卡片，请找管理员喵!"

        # 发送卡片介绍
        await update.effective_message.reply_html(msg)

    async def cmd_my_cards(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /mycards", getattr(user, "id", None))

        # 获取用户卡片
        user_cards: list = self.db.get_user_cards(user.id)
        # 获取所有卡片
        all_cards: list = self.cards.get("cards", default=[])
        # 统计每张卡片的数量
        card_counts = {}
        for card_name in user_cards:
            card_counts[card_name] = card_counts.get(card_name, default=0) + 1
        # 格式化卡片介绍
        lines = []
        warnings = []
        for card_name, count in card_counts.items():
            # 查找对应的完整卡片信息
            card_info = next((c for c in all_cards if c["name"] == card_name), None)
            if card_info:
                lines.append(
                    f"{card_info['emoji']} <b>{card_info['name']}</b> — 数量: {count}"
                )
            else:
                lines.append(f"<b>{card_name}</b> — 数量: {count}")
                warnings.append(f"卡片 {card_name}")

        if not lines:
            lines.append("你还没有任何卡片，快去购买吧！")

        msg = f"📰 <b>我的卡片</b>\n\n" + "\n".join(lines)

        # 添加警告信息
        if warnings:
            msg += "\n\n⚠️ <b>警告：</b>"
            for warning in warnings:
                msg += f"{warning} 未找到\n"

        # 发送卡片介绍
        await update.effective_message.reply_html(msg)

    async def cmd_buy_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info("用户 %s 执行了命令 /buycard", getattr(user, "id", None))

        # 获取命令参数
        args = context.args or []
        if not args:
            await update.effective_message.reply_html(
                "请指定要购买的卡片名称，例如：/buycard xxx"
            )
            return

        # 获取卡片名称
        card_name = " ".join(args)
        # 获取所有卡片
        all_cards: list = self.cards.get("cards", default=[])
        # 查找对应的卡片信息
        card_info = next((c for c in all_cards if c["name"] == card_name), None)

        if not card_info:
            await update.effective_message.reply_html(f"未找到卡片：{card_name}")
            return

        # 获取卡片价格
        card_point = card_info.get("point", default=0)
        if card_point <= 0:
            await update.effective_message.reply_html(
                f"卡片 {card_name} 价格未设置，无法购买"
            )
            return

        # 获取用户当前经验值
        user_exp = self.db.get_user_exp(user.id)
        if user_exp < card_point:
            await update.effective_message.reply_html(
                f"经验值不足！需要 {card_point} 经验值，当前只有 {user_exp} 经验值"
            )
            return

        # 消耗经验值
        self.db.add_user_exp(user.id, -card_point)
        # 添加卡片
        self.db.add_user_card(user.id, card_name)
        logger.info(
            "用户 %s 购买了卡片: %s，消耗了 %s 经验值", user.id, card_name, card_point
        )

        # 回复用户
        user_name = user.full_name or user.username or f"用户{user.id}"
        card_msg = f"🎁 <b>恭喜 <a href='tg://user?id={user.id}'>{user_name}</a> 购买成功！</b>\n\n{card_info['emoji']} <b>{card_info['name']}</b>\n{card_info['description']}\n\n消耗了 {card_point} 经验值，剩余 {user_exp - card_point} 经验值\n\n现在你可以使用这张卡片了！"
        await update.effective_message.reply_html(card_msg)

    def _calculate_level_from_exp(self, exp):
        """
        根据经验值计算用户等级
        使用 delta 格式的等级配置
        """
        level_configs = self.levels.get("levels", default=[])
        if not level_configs:
            return 1

        # 计算每个等级需要的总经验值
        total_exp_needed = 0
        for i, level_config in enumerate(level_configs):
            delta = level_config.get("delta", default=0)
            total_exp_needed += delta
            if exp < total_exp_needed:
                return i + 1

        # 如果经验值超过所有等级配置，返回最高等级
        return len(level_configs) + 1

    def _get_next_level_exp_needed(self, current_level):
        """
        获取下一等级需要的总经验值
        使用 delta 格式的等级配置
        """
        level_configs = self.levels.get("levels", default=[])

        if current_level - 1 >= len(level_configs):
            # 已经是最高等级
            return 0

        # 计算到下一等级需要的总经验值
        total_exp_needed = 0
        for i in range(current_level):
            if i < len(level_configs):
                total_exp_needed += level_configs[i].get("delta", default=0)

        return total_exp_needed

    async def check_user_level_up(self, user, update, context):
        """
        检查用户是否应该升级
        """
        try:
            # 获取用户当前的经验值和等级
            user_exp = self.db.get_user_exp(user.id)
            current_level = self.db.get_user_level(user.id)

            # 计算用户应该达到的等级
            target_level = self._calculate_level_from_exp(user_exp)

            # 如果用户的等级低于应该达到的等级，就升级
            if target_level > current_level:
                # 更新用户等级
                self.db.set_user_level(user.id, target_level)
                logger.info("用户 %s 升级到了等级 %d", user.id, target_level)

                # 回复用户
                user_name = user.full_name or user.username or f"用户{user.id}"
                level_up_msg = f"🎉 <b>恭喜 <a href='tg://user?id={user.id}'>{user_name}</a> 升级了！</b>\n\n你现在是 <b>等级 {target_level}</b> 了！\n\n继续努力，解锁更多等级和成就吧！"
                await update.effective_message.reply_html(level_up_msg)
        except Exception as e:
            logger.exception("检查用户升级时发生错误: %s", e)

    async def _add_exp(self, user, chat, msg_type, ts, update, context):
        # compute points and daily cap
        points_map = self.cfg.get("experience", "points", default={})
        point = int(points_map.get(msg_type, points_map.get("text", default=1)))
        daily_limit = int(self.cfg.get("experience", "daily_limit", default=150) or 150)

        # today's range
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = int(today_start.timestamp())
        counts = self.db.get_user_counts(user.id, start_ts=start_ts, end_ts=None)
        # compute current earned today
        earned_today = 0
        for t, cnt in counts.items():
            if t == "total":
                continue
            p = int(points_map.get(t, points_map.get("text", default=1)))
            earned_today += p * cnt

        to_add = 0
        if earned_today < daily_limit:
            allowed = daily_limit - earned_today
            to_add = min(point, allowed)

        # record message and add exp
        try:
            self.db.record_message(user.id, chat.id, msg_type, ts)
            logger.debug("记录了用户 %s 在 %s 中的消息", user.id, chat.id)
        except Exception:
            logger.exception(
                "无法记录用户 %s 在 %s 中的消息", getattr(user, "id", None), chat.id
            )

        if to_add > 0:
            try:
                self.db.add_user_exp(user.id, to_add)
                logger.info("添加了 %s 经验给用户 %s", to_add, user.id)

                # 检查用户是否应该升级
                await self.check_user_level_up(user, update, context)
            except Exception:
                logger.exception(
                    "无法添加经验 %s 给用户 %s", to_add, getattr(user, "id", None)
                )

    async def _unlock_achievement(self, user, chat, msg_type, ts, m):
        try:
            # 获取用户的当前统计数据
            user_counts = self.db.get_user_counts(user.id, start_ts=None, end_ts=None)
            total_messages = user_counts.get("total", default=0)
            image_count = user_counts.get("photo", default=0)
            sticker_count = user_counts.get("sticker", default=0)

            # 获取所有成就
            all_achievements = self.achievements.get("achievements")
            # 获取用户已有的成就
            user_achievements = self.db.get_user_achievements(user.id)
            user_achievement_names = [a["name"] for a in user_achievements]

            # 检查每个成就的解锁条件
            for achievement in all_achievements:
                name = achievement["name"]
                emoji = achievement["emoji"]
                description = achievement["description"]
                condition = achievement.get("type", default=[])

                # 跳过用户已有的成就
                if name in user_achievement_names:
                    continue

                # 检查成就条件
                # 检查成就条件
                unlocked = False
                if len(condition) == 3:
                    condition_type, operator, target = condition

                    if condition_type == "send_message_count" and operator == ">=":
                        if total_messages >= int(target):
                            unlocked = True
                    elif condition_type == "send_image_count" and operator == ">=":
                        if image_count >= int(target):
                            unlocked = True
                    elif condition_type == "send_sticker_count" and operator == ">=":
                        if sticker_count >= int(target):
                            unlocked = True

                # 如果解锁了新成就
                if unlocked:
                    # 为用户添加成就
                    self.db.add_user_achievement(user.id, name, ts)
                    logger.info("用户 %s 解锁了成就: %s", user.id, name)

                    # 回复用户
                    user_name = user.full_name or user.username or f"用户{user.id}"
                    achievement_msg = f"🎉 <b>恭喜 <a href='tg://user?id={user.id}'>{user_name}</a> 解锁新成就！</b>\n\n{emoji} <b>{name}</b>\n{description}\n\n继续努力解锁更多成就吧！"
                    await m.reply_html(achievement_msg)

                    # 更新用户成就列表，避免重复检查
                    user_achievement_names.append(name)
        except Exception as e:
            logger.exception("检查成就时发生错误: %s", e)

    async def _unlock_badge(self, user, chat, m, ts):
        try:
            # 获取用户的上一条消息记录
            # 这里需要在database.py中添加一个方法来获取用户的上一条消息
            # 暂时简化处理，通过检查用户今天是否已经获得过徽章来判断
            # 实际应该检查上一条消息的时间戳

            # 获取今日的开始时间
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today_ts = int(today_start.timestamp())

            # 获取用户今天的徽章记录
            # 这里需要在database.py中添加一个方法来获取用户今天的徽章
            # 暂时简化处理，检查用户是否已经有任何徽章
            # 实际应该检查今天是否已经获得过徽章
            user_badge_names = self.db.get_user_badges(user.id)

            # 检查用户今天是否已经发送过消息
            today_counts = self.db.get_user_counts(
                user.id, start_ts=today_ts, end_ts=None
            )
            today_messages = today_counts.get("total", default=0)

            # 如果用户今天已经发送过消息，说明不是第一条消息，跳过徽章检查
            # 这样可以确保只有每天的第一条消息才会触发徽章检查
            if today_messages > 1:
                pass
            else:
                # 获取用户的今日统计数据
                today_stickers = today_counts.get("sticker", default=0)

                # 获取所有徽章
                all_badges = self.badges.get("badges", default=[])

                # 检查每个徽章的获取条件
                for badge in all_badges:
                    name = badge["name"]
                    emoji = badge["emoji"]
                    description = badge["description"]
                    condition = badge.get("type", default=[])

                    # 跳过用户已有的徽章
                    if name in user_badge_names:
                        continue

                    # 检查徽章条件
                    earned = False
                    if len(condition) == 3:
                        condition_type, operator, target = condition

                        if (
                            condition_type == "send_message_top"
                            and operator == "=="
                            and target == "1"
                        ):
                            # 获取今日消息排行榜
                            chat_id = chat.id if chat else None
                            if chat_id:
                                leaderboard = self.db.get_leaderboard(
                                    chat_id, start_ts=today_ts, end_ts=None, limit=1
                                )
                                if leaderboard and leaderboard[0]["user_id"] == user.id:
                                    earned = True
                        elif (
                            condition_type == "send_sticker_top"
                            and operator == "=="
                            and target == "1"
                        ):
                            chat_id = chat.id if chat else None
                            if chat_id:
                                sticker_leaderboard = self.db.get_sticker_leaderboard(
                                    chat_id, start_ts=today_ts, end_ts=None, limit=1
                                )
                                if (
                                    sticker_leaderboard
                                    and sticker_leaderboard[0]["user_id"] == user.id
                                ):
                                    earned = True

                    if earned:
                        # 为用户添加徽章
                        self.db.add_user_badges(user.id, [name], ts)
                        logger.info("用户 %s 获得了徽章: %s", user.id, name)

                        user_name = user.full_name or user.username or f"用户{user.id}"
                        badge_msg = f"🏅 <b>恭喜 <a href='tg://user?id={user.id}'>{user_name}</a> 获得新徽章！</b>\n\n{emoji} <b>{name}</b>\n{description}\n\n继续努力获得更多徽章吧！"
                        await m.reply_html(badge_msg)

                        user_badge_names.append(name)
        except Exception as e:
            logger.exception("检查徽章时发生错误: %s", e)
