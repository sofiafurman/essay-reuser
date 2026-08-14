import sqlite3
import json

db_path = "reuser.db"

def init_db():
    conn = sqlite3.connect(db_path)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS essays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT,
        embedding TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_essays(application, prompt, response, embedding):
    conn = sqlite3.connect(db_path)

    embedding_json = json.dumps(embedding)

    conn.execute(
        """
        INSERT INTO essays (application, prompt, response, embedding)
        VALUES (?, ?, ?, ?)
        """,
        (application, prompt, response, embedding_json)
    )

    conn.commit()
    conn.close()

def get_essays():
    conn = sqlite3.connect(db_path)

    essays = conn.execute(
        "SELECT id, application, prompt, response, embedding FROM essays"
    ).fetchall()

    conn.close()

    return essays
    