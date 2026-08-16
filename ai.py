import os
import math
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

    prompt = """
    Describe an experience communicating with someone whose
    background or perspective differed from your own.
    """

    ranked = rank_chunks(prompt, chunks)

    for chunk in ranked:
        print("\nScore:", round(chunk["similarity_score"], 3))
        print("Essay ID:", chunk["essay_id"])
        print("Chunk:", chunk["chunk_index"])
        print(chunk["text"])