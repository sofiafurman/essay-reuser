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

    conn.execute("""
    CREATE TABLE IF NOT EXISTS essay_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        essay_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        embedding TEXT NOT NULL,
        FOREIGN KEY (essay_id) REFERENCES essays(id)
        )
        """)
    

    conn.commit()
    conn.close()

def save_essays(application, prompt, response, embedding):
    conn = sqlite3.connect(db_path)

    embedding_json = json.dumps(embedding)

    cursor = conn.execute(
        """
        INSERT INTO essays (application, prompt, response, embedding)
        VALUES (?, ?, ?, ?)
        """,
        (application, prompt, response, embedding_json)
    )

    essay_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return essay_id

def get_essays():
    conn = sqlite3.connect(db_path)

    essays = conn.execute(
        "SELECT id, application, prompt, response, embedding FROM essays"
    ).fetchall()

    conn.close()

    return essays

def save_chunks(essay_id, chunks, embeddings):
    conn = sqlite3.connect(db_path)

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        embedding_json = json.dumps(embedding)

        conn.execute(
            """
            INSERT INTO essay_chunks (essay_id, chunk_index, text, embedding)
            VALUES (?, ?, ?, ?)
            """,
            (essay_id, i, chunk, embedding_json)
        )
        #zip(chunks,embeddings) pairs them, i.e. chunk 0 to embedding 0
        #enumerate is row numbers starting from one, chunk index is already there

    conn.commit()
    conn.close()


def get_chunks():
    conn = sqlite3.connect(db_path)

    chunks = conn.execute(
        "SELECT id, essay_id, chunk_index, text, embedding FROM essay_chunks"
    ).fetchall()

    conn.close()

    return chunks