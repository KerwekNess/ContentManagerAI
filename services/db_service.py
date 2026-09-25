import sqlite3
import json
from datetime import datetime

class DBService:
    def __init__(self, settings):
        self.db_path = settings.DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    style TEXT NOT NULL,
                    ideas TEXT,
                    post_text TEXT,
                    titles TEXT,
                    hashtags TEXT,
                    created_at TEXT
                )''')

    def save_generation(self, topic, style, ideas, post_text, titles, hashtags):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO generations (topic, style, ideas, post_text, titles, hashtags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (topic, style, json.dumps(ideas, ensure_ascii=False), post_text, json.dumps(titles, ensure_ascii=False), hashtags, created_at))

    def get_history(self, limit=20):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute('SELECT * FROM generations ORDER BY id DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
            history = []
            for row in rows:
                history.append({
                    'id': row['id'],
                    'topic': row['topic'],
                    'style': row['style'],
                    'ideas': json.loads(row['ideas']),
                    'post_text': row['post_text'],
                    'titles': json.loads(row['titles']),
                    'hashtags': row['hashtags'],
                    'created_at': row['created_at']
                })
            return history
