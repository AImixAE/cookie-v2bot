import sqlite3
from pathlib import Path
from typing import Optional, Any
import time


class Database:
    def __init__(self, db_path: str | Path = "data/chat.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                total_exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                title TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                msg_type TEXT,
                ts INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
            )
            """
        )

        # 用户获得的成就表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement TEXT,
                ts INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, achievement)
                )
            """
        )

        # 用户获得的徽章表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge TEXT,
                ts INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """
        )

        # 用户的卡片
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card TEXT,
                ts INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """
        )

        self.conn.commit()

    def close(self):
        self.conn.close()

    def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
    ):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO users(user_id, username, first_name, last_name, level)
            VALUES(?,?,?,?,1)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
            first_name=excluded.first_name, last_name=excluded.last_name
            """,
            (user_id, username, first_name, last_name),
        )
        self.conn.commit()

    def set_user_exp(self, user_id: int, exp: int):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE users SET total_exp = ? WHERE user_id = ?
            """,
            (exp, user_id),
        )
        self.conn.commit()

    def add_user_exp(self, user_id: int, exp: int):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE users SET total_exp = total_exp + ? WHERE user_id = ?
            """,
            (exp, user_id),
        )
        self.conn.commit()

    def get_user_exp(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT total_exp FROM users WHERE user_id = ?",
            (user_id,),
        )
        result = cur.fetchone()
        return result["total_exp"] if result else 0

    def get_user_level(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT level FROM users WHERE user_id = ?",
            (user_id,),
        )
        result = cur.fetchone()
        return result["level"] if result else 1

    def set_user_level(self, user_id: int, level: int):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE users SET level = ? WHERE user_id = ?",
            (level, user_id),
        )
        self.conn.commit()

    def delete_user(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM users WHERE user_id = ?",
            (user_id,),
        )
        self.conn.commit()

    def record_message(
        self,
        user_id: int,
        chat_id: int,
        msg_type: str,
        ts: Optional[int] = None,
    ):
        if ts is None:
            ts = int(time.time())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages(user_id, chat_id, msg_type, ts)
            VALUES(?,?,?,?)
            """,
            (user_id, chat_id, msg_type, ts),
        )
        self.conn.commit()

    def get_user_counts(
        self,
        user_id: int,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> dict[str, Any]:
        q = "SELECT msg_type, COUNT(*) as cnt FROM messages WHERE user_id = ?"
        params = [user_id]
        if start_ts is not None:
            q += " AND ts >= ?"
            params.append(start_ts)
        if end_ts is not None:
            q += " AND ts <= ?"
            params.append(end_ts)
        q += " GROUP BY msg_type"
        cur = self.conn.cursor()
        cur.execute(q, params)
        rows = cur.fetchall()
        res = {r["msg_type"]: r["cnt"] for r in rows}
        # total messages
        cur.execute(
            "SELECT COUNT(*) as total FROM messages WHERE user_id = ?"
            + (" AND ts >= ?" if start_ts is not None else "")
            + (" AND ts < ?" if end_ts is not None else ""),
            params,
        )
        total = cur.fetchone()[0]
        res["total"] = total
        return res

    def get_leaderboard(
        self,
        chat_id: int,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: int = 10,
    ):
        q = "SELECT user_id, COUNT(*) as cnt FROM messages WHERE chat_id = ?"
        params = [chat_id]
        if start_ts is not None:
            q += " AND ts >= ?"
            params.append(start_ts)
        if end_ts is not None:
            q += " AND ts < ?"
            params.append(end_ts)
        q += " GROUP BY user_id ORDER BY cnt DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(q, params)
        return cur.fetchall()

    def get_sticker_leaderboard(
        self,
        chat_id: int,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: int = 10,
    ):
        q = "SELECT user_id, COUNT(*) as cnt FROM messages WHERE chat_id = ? AND msg_type = 'sticker'"
        params = [chat_id]
        if start_ts is not None:
            q += " AND ts >= ?"
            params.append(start_ts)
        if end_ts is not None:
            q += " AND ts < ?"
            params.append(end_ts)
        q += " GROUP BY user_id ORDER BY cnt DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(q, params)
        return cur.fetchall()

    def get_photo_leaderboard(
        self,
        chat_id: int,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: int = 10,
    ):
        q = "SELECT user_id, COUNT(*) as cnt FROM messages WHERE chat_id = ? AND msg_type = 'photo'"
        params = [chat_id]
        if start_ts is not None:
            q += " AND ts >= ?"
            params.append(start_ts)
        if end_ts is not None:
            q += " AND ts < ?"
            params.append(end_ts)
        q += " GROUP BY user_id ORDER BY cnt DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(q, params)
        return cur.fetchall()

    def get_total_messages(
        self, start_ts: Optional[int] = None, end_ts: Optional[int] = None
    ) -> int:
        q = "SELECT COUNT(*) FROM messages"
        params = []
        if start_ts is not None or end_ts is not None:
            q += " WHERE"
            parts = []
            if start_ts is not None:
                parts.append(" ts >= ?")
                params.append(start_ts)
            if end_ts is not None:
                parts.append(" ts < ?")
                params.append(end_ts)
            q += " AND".join(parts)
        cur = self.conn.cursor()
        cur.execute(q, params)
        return cur.fetchone()[0]

    def get_known_chats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT chat_id FROM messages")
        return [r[0] for r in cur.fetchall()]

    def get_chats_info(self):
        """Return list of rows:
        (chat_id, message_count, last_ts, title, total_exp)"""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT m.chat_id, COUNT(*) as cnt, MAX(m.ts) as last_ts, c.title,
                   SUM(CASE 
                       WHEN m.msg_type = 'photo' THEN 3
                       WHEN m.msg_type = 'sticker' THEN 2
                       WHEN m.msg_type = 'voice' THEN 3
                       ELSE 1
                   END) as total_exp
            FROM messages m
            LEFT JOIN chats c ON m.chat_id = c.chat_id
            GROUP BY m.chat_id
            """
        )
        return cur.fetchall()

    def upsert_chat(self, chat_id: int, title: str | None):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO chats(chat_id, title) VALUES(?,?)
            ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title
            """,
            (chat_id, title),
        )
        self.conn.commit()

    def clear_database(self):
        """Clear the database file and recreate schema.
        Use with confirmation."""
        # Close the current connection
        try:
            if self.conn:
                self.conn.close()
            # Add a small delay to ensure file is released on Windows
            time.sleep(0.1)
        except Exception as e:
            print(f"Failed to close connection: {e}")

        # Delete the database file
        if self.db_path.exists():
            try:
                self.db_path.unlink()
                print(f"Database file deleted: {self.db_path}")
            except Exception as e:
                print(f"Failed to delete database file: {e}")
                raise RuntimeError(f"无法删除数据库文件: {e}")

        # Recreate connection and schema
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        print("Database recreated with new schema")

    def get_user_by_id(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()

    def get_all_users(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY total_exp DESC")
        return cur.fetchall()

    def get_leaderboard_with_names(
        self,
        chat_id: int,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: int = 10,
        sort_by: str = "exp",
    ):
        q = """
        SELECT m.user_id, u.username, u.first_name, u.last_name,
               SUM(CASE 
                   WHEN m.msg_type = 'photo' THEN 3
                   WHEN m.msg_type = 'sticker' THEN 2
                   WHEN m.msg_type = 'voice' THEN 3
                   ELSE 1
               END) as exp,
               COUNT(*) as cnt
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.chat_id = ?
        """
        params = [chat_id]
        if start_ts is not None:
            q += " AND m.ts >= ?"
            params.append(start_ts)
        if end_ts is not None:
            q += " AND m.ts < ?"
            params.append(end_ts)
        order_by = "exp" if sort_by == "exp" else "cnt"
        q += f" GROUP BY m.user_id ORDER BY {order_by} DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(q, params)
        return cur.fetchall()

    def add_user_achievement(
        self,
        user_id: int,
        achievement: str,
        ts: Optional[int] = None,
    ):
        if ts is None:
            ts = int(time.time())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO achievements(user_id, achievement, ts) VALUES(?,?,?)
            ON CONFLICT(user_id, achievement) DO NOTHING
            """,
            (user_id, achievement, ts),
        )
        self.conn.commit()

    def get_user_achievements(self, user_id: int) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT achievement, ts FROM achievements WHERE user_id = ?
            """,
            (user_id,),
        )
        return [{"name": r[0], "ts": r[1]} for r in cur.fetchall()]

    def get_user_achievement_count(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM achievements WHERE user_id = ?
            """,
            (user_id,),
        )
        return cur.fetchone()[0]

    def add_user_badges(
        self, user_id: int, badges: list[str], ts: Optional[int] = None
    ):
        if ts is None:
            ts = int(time.time())
        cur = self.conn.cursor()
        for badge in badges:
            cur.execute(
                """
                INSERT INTO badges(user_id, badge, ts) VALUES(?,?,?)
                """,
                (user_id, badge, ts),
            )
        self.conn.commit()

    def get_user_badges(self, user_id: int) -> list[str]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT badge FROM badges WHERE user_id = ?
            """,
            (user_id,),
        )
        return [r[0] for r in cur.fetchall()]

    def get_user_badge_count(self, user_id: int, badge: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM badges WHERE user_id = ? AND badge = ?
            """,
            (user_id, badge),
        )
        return cur.fetchone()[0]

    def get_user_badges_count(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM badges WHERE user_id = ?
            """,
            (user_id,),
        )
        return cur.fetchone()[0]

    def get_user_badges_with_ts(self, user_id: int) -> list[tuple[str, int]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT badge, ts FROM badges WHERE user_id = ?
            """,
            (user_id,),
        )
        return cur.fetchall()

    def add_user_card(
        self,
        user_id: int,
        card: str,
        ts: Optional[int] = None,
    ):
        if ts is None:
            ts = int(time.time())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO cards(user_id, card, ts) VALUES(?,?,?)
            """,
            (user_id, card, ts),
        )
        self.conn.commit()

    def get_user_cards(self, user_id: int) -> list[str]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT card FROM cards WHERE user_id = ?
            """,
            (user_id,),
        )
        return [r[0] for r in cur.fetchall()]

    def get_user_cards_count(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM cards WHERE user_id = ?
            """,
            (user_id,),
        )
        return cur.fetchone()[0]

    def get_user_card_count(self, user_id: int, card: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM cards WHERE user_id = ? AND card = ?
            """,
            (user_id, card),
        )
        return cur.fetchone()[0]

    def use_user_card(self, user_id: int, card: str) -> bool:
        """
        使用用户的一张卡片，删除一个实例
        返回是否成功使用
        """
        # 先检查用户是否有这张卡片
        if self.get_user_card_count(user_id, card) <= 0:
            return False

        # 删除一张卡片（使用LIMIT 1确保只删除一个）
        cur = self.conn.cursor()
        cur.execute(
            """
            DELETE FROM cards WHERE user_id = ? AND card = ? LIMIT 1
            """,
            (user_id, card),
        )
        self.conn.commit()
        return True
