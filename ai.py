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

def create_embedding(text):
    result = client.embeddings.create(
        model = "text-embedding-3-small",
        input=text
    )
    return result.data[0].embedding

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
    from database import get_essays

    essays = get_essays()

    new_prompt = """
    Describe a time you realized your first approach to a problem was wrong.
    What did you change, and what did you learn?
    """
    prompts = ["Tell us about a way you have helped make a community more accessible or welcoming to others.", "Describe an experience that taught you the importance of using evidence when making decisions.", "Tell us about an experience that changed how you think about making a meaningful impact."]

    for prompt in prompts:
        print("\nPROMPT:", prompt)
        ranked = rank_essays(prompt, essays)
        for essay in ranked:
            print(
                essay["application"],
                round(essay["similarity_score"], 3)
            )
    '''test_prompt = "Describe a time you demonstrated leadership."
    test_response = """Lorem ipsum"""
    summary = summarize_essay(test_prompt, test_response)
    print(summary)'''