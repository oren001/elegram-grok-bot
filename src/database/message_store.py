import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class MessageDatabase:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.setup_database()
    
    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                username TEXT,
                message_text TEXT,
                timestamp DATETIME,
                is_bot_mention BOOLEAN
            )
        ''')
        self.conn.commit()

    def store_message(self, chat_id: int, user_id: int, username: str, 
                     message_text: str, is_bot_mention: bool) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO messages (chat_id, user_id, username, message_text, timestamp, is_bot_mention)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (chat_id, user_id, username, message_text, datetime.now(), is_bot_mention))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing message: {e}")
            return False

    def get_recent_context(self, chat_id: int, limit: int = 10) -> List[Tuple[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT username, message_text FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (chat_id, limit))
        return cursor.fetchall()
