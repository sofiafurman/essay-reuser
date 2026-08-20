import os
import math
import json

from dotenv import load_dotenv
from openai import OpenAI

from pydantic import BaseModel
from typing import List, Literal, Optional

from database import get_chunks

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class ChunkMatch(BaseModel):
    essay_id: int
    chunk_index: int
    classification: Literal["REUSE", "ADAPT", "SUPPORTING"]
    reason: str
    adaptation_needed: Optional[str]

class EssayMatch(BaseModel):
    essay_id: int
    classification: Literal["REUSE", "ADAPT"]
    reason: str
    adaptation_needed: str

class MatchAnalysis(BaseModel):
    essay_matches: List[EssayMatch]
    chunk_matches: List[ChunkMatch]

def rank_essays(prompt_embedding, essays):
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

def rank_chunks(prompt_embedding, chunks):
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

def analyze_matches(new_prompt, ranked_essays, ranked_chunks):
    top_chunks = ranked_chunks[:5]
    top_essays = ranked_essays[:3]

    retrieved_chunks = ""

    for chunk in top_chunks:
        retrieved_chunks += f"""
ESSAY ID: {chunk["essay_id"]}
CHUNK {chunk["chunk_index"]}:
{chunk["text"]}

---
"""

    retrieved_essays = ""

    for essay in top_essays:
        retrieved_essays += f"""
ESSAY ID: {essay["id"]}
ORIGINAL PROMPT: {essay["prompt"]}
RESPONSE:
{essay["response"]}

---
"""

    instructions = f"""
You are helping a student identify writing from previous application
essays that may be reused for a new application prompt.

NEW PROMPT:
{new_prompt}

CANDIDATE WHOLE ESSAYS:
{retrieved_essays}

CANDIDATE PASSAGES:
{retrieved_chunks}

Evaluate whole essays and individual passages independently.

WWHOLE ESSAYS:

REUSE means the overall essay already substantially answers the new
prompt and could serve as its basis with relatively minor changes.

ADAPT means the existing experience genuinely contains evidence that can
answer the new prompt, but the framing, structure, emphasis, or reflection
would need meaningful changes.

Do not classify material as ADAPT merely because it could hypothetically
be reframed to address the prompt. The necessary connection must already
be supported by details in the student's existing writing.

If answering the new prompt would require inventing a new motivation,
impact, lesson, relationship, outcome, or significance, do not return
the material.

Only recommend a whole essay if the overall essay is genuinely useful.
Do not return weak or irrelevant essays.


PASSAGES:

REUSE means the passage itself directly provides material needed to
answer the new prompt and could be reused with relatively minor changes.

ADAPT requires that the useful connection already exists in the passage
or its source essay. Do not recommend a passage based on a hypothetical
connection that is not supported by the student's writing.

SUPPORTING means the passage is useful as context, setup, transition, or
support for a recommended whole essay, but would not be worth recommending
as reusable material on its own.

Only return passages that are REUSE, ADAPT, or meaningfully SUPPORTING.
Do not return irrelevant passages.

A passage from an essay may be useful even if the whole essay is not
recommended.

A whole essay recommendation and passage recommendations from that same
essay may both be returned when appropriate.

Do not invent experiences, details, outcomes, or reflections.
Do not write a new essay.
"""

    result = client.responses.parse(
        model="gpt-5-nano",
        input=instructions,
        text_format = MatchAnalysis
    )

    return result.output_parsed
