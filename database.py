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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application TEXT NOT NULL,
            prompt TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
            """)

    conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                essay_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                classification TEXT NOT NULL,
                reason TEXT NOT NULL,
                adaptation_needed TEXT NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id),
                FOREIGN KEY (essay_id) REFERENCES essays(id)
            )
                """)

    conn.commit()
    conn.close()

def get_prompt(prompt_id):
    conn = sqlite3.connect(db_path)

    prompt = conn.execute(
        """
        SELECT id, application, prompt
        FROM prompts
        WHERE id = ?
        """,
        (prompt_id,)
    ).fetchone()

    conn.close()

    return prompt

def get_analysis_details(prompt_id):
    conn = sqlite3.connect(db_path)

    analyses = conn.execute(
        """
        SELECT
            analyses.classification,
            analyses.reason,
            analyses.adaptation_needed,
            essays.application,
            essays.prompt,
            essay_chunks.text
        FROM analyses
        JOIN essays
            ON analyses.essay_id = essays.id
        JOIN essay_chunks
            ON analyses.essay_id = essay_chunks.essay_id
            AND analyses.chunk_index = essay_chunks.chunk_index
        WHERE analyses.prompt_id = ?
        """,
        (prompt_id,)
    ).fetchall()

    conn.close()

    return analyses

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

def save_prompt(application, prompt, embedding):
    conn = sqlite3.connect(db_path)

    embedding_json = json.dumps(embedding)

    cursor = conn.execute(
        """
        INSERT INTO prompts (application, prompt, embedding)
        VALUES (?, ?, ?)
        """,
        (application, prompt, embedding_json)
    )
    prompt_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return prompt_id

def get_prompts():
    conn = sqlite3.connect(db_path)

    prompts = conn.execute(
        "SELECT id, application, prompt, embedding FROM prompts"
    ).fetchall()

    conn.close()

    return prompts

def get_analyses(prompt_id):
    conn = sqlite3.connect(db_path)

    analyses = conn.execute(
        """
        SELECT essay_id, chunk_index, classification, reason, adaptation_needed
        FROM analyses
        WHERE prompt_id = ?
        """,
        (prompt_id,)
    ).fetchall()

    conn.close()

    return analyses

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

def save_analysis(prompt_id, analysis):
    conn = sqlite3.connect(db_path)

    for match in analysis.matches:
        conn.execute(
            """
            INSERT INTO analyses (
                prompt_id,
                essay_id,
                chunk_index,
                classification,
                reason,
                adaptation_needed
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                prompt_id,
                match.essay_id,
                match.chunk_index,
                match.classification,
                match.reason,
                match.adaptation_needed
            )
        )
    conn.commit()
    conn.close()
        
def get_chunks():
    conn = sqlite3.connect(db_path)

    chunks = conn.execute(
        "SELECT id, essay_id, chunk_index, text, embedding FROM essay_chunks"
    ).fetchall()

    conn.close()

    return chunks