import sqlite3

db_path = "reuser.db"

def init_db():
    conn = sqlite3.connect(db_path)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS essays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT,
        summary TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_essays(application, prompt, response, summary):
    conn = sqlite3.connect(db_path)

    conn.execute(
        """
        INSERT INTO essays (application, prompt, response, summary)
        VALUES (?, ?, ?, ?)
        """,
        (application, prompt, response, summary)
    )

    conn.commit()
    conn.close()

def get_essays():
    conn = sqlite3.connect(db_path)

    essays = conn.execute(
        "SELECT id, application, prompt, response, summary FROM essays"
    ).fetchall()

    conn.close()

    return essays
    