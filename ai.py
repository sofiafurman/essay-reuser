import os
import math
import json

from dotenv import load_dotenv
from openai import OpenAI

from pydantic import BaseModel
from typing import List, Literal

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class ChunkMatch(BaseModel):
    essay_id: int
    chunk_index: int
    classification: Literal["REUSE", "ADAPT"]
    reason: str
    adaptation_needed: str

class MatchAnalysis(BaseModel):
    matches: List[ChunkMatch]

def rank_essays(new_prompt, essays):
    prompt_embedding = create_embedding(new_prompt)
    ranked = []

    for essay in essays:
        essay_id, application, old_prompt, response, embedding_json = essay

        essay_embedding = json.loads(embedding_json)

        similarity_score = cosine_similarity(prompt_embedding, essay_embedding)

        ranked.append({
            "id": essay_id,
            "application": application,
            "prompt": old_prompt,
            "response": response,
            "similarity_score": similarity_score
        })

    ranked.sort(
        key=lambda essay: essay["similarity_score"],
        reverse=True
    )

    return ranked

def rank_chunks(new_prompt, chunks):
    prompt_embedding = create_embedding(new_prompt)
    ranked = []

    for chunk in chunks:
        chunk_id, essay_id, chunk_index, text, embedding_json = chunk

        chunk_embedding = json.loads(embedding_json)

        similarity_score = cosine_similarity(prompt_embedding, chunk_embedding)

        ranked.append({
            "chunk_id": chunk_id,
            "essay_id": essay_id,
            "chunk_index": chunk_index,
            "text": text,
            "similarity_score": similarity_score
        })


    ranked.sort(
            key=lambda essay: essay["similarity_score"],
            reverse=True
        )

    return ranked

def create_embedding(text):  
    result = client.embeddings.create(
        model = "text-embedding-3-small",
        input=text
    )
    return result.data[0].embedding

def create_embeddings(texts):
    result = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    return [item.embedding for item in result.data]

def split_essay(text):
    paras = text.split("\n")

    chunks = []

    for para in paras:
        para = para.strip()
        if para:
            chunks.append(para)

    return chunks

def cosine_similarity(vec_a, vec_b): #compare embeddings
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    return dot_product / (magnitude_a * magnitude_b)

def analyze_matches(new_prompt, ranked_chunks):
    top_chunks = ranked_chunks[:5]

    retrieved_text = ""

    for chunk in top_chunks:
        retrieved_text += f"""
ESSAY ID: {chunk["essay_id"]}
CHUNK {chunk["chunk_index"]}:
{chunk["text"]}

---
"""

    instructions = f"""
You are helping a student reuse material from their previous application
essays for a new application prompt.

NEW PROMPT:
{new_prompt}

RETRIEVED PREVIOUS WRITING:
{retrieved_text}

Analyze which retrieved material is genuinely useful for answering the
new prompt.

For each useful piece of material:
- identify the essay ID and chunk
- classify it as REUSE, ADAPT, or WEAK
- explain briefly why it is relevant
- explain what would need to change for the new prompt

Only include material classified as REUSE or ADAPT.

REUSE means the existing material directly addresses an important part
of the new prompt and could be reused with relatively minor changes.

ADAPT means the underlying experience or idea is useful, but its framing,
emphasis, or reflection needs meaningful changes.

Do not include weak or irrelevant material.
Do not invent experiences, details, outcomes, or reflections.
Do not write a new essay.
"""

    result = client.responses.parse(
        model="gpt-5-nano",
        input=instructions,
        text_format = MatchAnalysis
    )

    return result.output_parsed


'''def summarize_essay(prompt, response):
    instructions = f"""
    Analyze the application response below for future reuse in other
    application essays.

    ORIGINAL PROMPT:
    {prompt}

    RESPONSE:
    {response}

    Write one concise, information-dense paragraph optimized for semantic
    retrieval.

    Include specific experiences, the student's actions and role, outcomes,
    reflections or changes in perspective, and themes when they are actually
    present.

    If a category is not present, simply omit it rather than stating that it
    is missing.

    Do not evaluate the quality of the writing.
    Do not invent information.
    Do not exceed 80 words.
    Do not begin/end with questions or affirmations: ONLY the content summary.
    """

    result = client.responses.create(
        model="gpt-5-nano",
        input=instructions
    )

    return result.output_text'''

if __name__ == "__main__":
    from database import get_chunks

    chunks = get_chunks()

    new_prompt = """
    Describe an experience communicating with someone whose
    background or perspective differed from your own.
    """

    ranked = rank_chunks(new_prompt, chunks)

    analysis = analyze_matches(new_prompt, ranked)

    print(analysis)