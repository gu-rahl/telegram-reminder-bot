# File: db.py
import sqlite3
from datetime import datetime

DB_PATH = 'reminders.db'

CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS reminders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL,
    reminder_text   TEXT    NOT NULL,
    remind_at       TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'active',
    repeat          TEXT,
    repeat_interval INTEGER DEFAULT 1
);
'''

class ReminderDB:
    def __init__(self, path=DB_PATH):
        # Открываем соединение с БД
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.execute(CREATE_TABLE)
        self.conn.commit()

    def add_reminders(self, chat_id, text, slots, rpt, interval):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = self.conn.cursor()
        for dt in slots:
            c.execute(
                "INSERT INTO reminders (chat_id, reminder_text, remind_at, created_at, repeat, repeat_interval)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    chat_id,
                    text,
                    dt.strftime('%Y-%m-%d %H:%M:%S'),
                    now,
                    rpt,
                    interval
                )
            )
        self.conn.commit()

    def get_due(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = self.conn.cursor()
        c.execute(
            "SELECT id, chat_id, reminder_text, remind_at, repeat, repeat_interval "
            "FROM reminders WHERE status='active' AND remind_at<=?",
            (now,)
        )
        return c.fetchall()

    def update_reminder(self, rid, remind_at):
        c = self.conn.cursor()
        c.execute(
            "UPDATE reminders SET remind_at=?, status='active' WHERE id=?",
            (remind_at.strftime('%Y-%m-%d %H:%M:%S'), rid)
        )
        self.conn.commit()

    def mark_done(self, rid):
        c = self.conn.cursor()
        c.execute(
            "UPDATE reminders SET status='done' WHERE id=?",
            (rid,)
        )
        self.conn.commit()
