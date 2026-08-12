import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def summarize_essay(prompt, response):
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

    return result.output_text

if __name__ == "__main__":
    test_prompt = "Describe a time you demonstrated leadership."

    test_response = """
    During robotics season, two members of my programming team strongly disagreed about how we should approach our autonomous system. One wanted to rebuild our path-planning system from scratch, while the other argued that modifying our existing code was safer with competition only three weeks away. As programming lead, I thought my job was to settle the debate. I listened to both sides, decided that rebuilding was too risky, and told the team we would stick with the existing system.

Technically, the conflict was resolved. In reality, I had made it worse. The teammate who wanted to rebuild stopped contributing ideas during meetings, while the other became increasingly defensive whenever our code failed. I realized I had treated leadership as the authority to make decisions rather than the responsibility to help a team make good decisions together.

At our next meeting, I changed my approach. Instead of announcing a solution, I asked both programmers to identify what they believed was failing in our current system and what evidence would change their minds. We discovered that their disagreement was smaller than it seemed: both were primarily concerned about inconsistent turns during longer autonomous paths. We spent one practice testing the existing system against a small prototype of the proposed rewrite.

The prototype performed better, but rebuilding everything remained unrealistic. Together, we chose a hybrid approach, replacing the weakest portion of our path planning while preserving the code that already worked. I divided the implementation between the two programmers and took responsibility for integrating their changes.

By competition, our autonomous routine was substantially more consistent. More importantly, both teammates were proposing ideas again.

I entered the season thinking leadership meant being willing to make the difficult call. I left understanding that decisiveness has its place, but leadership can also mean creating a process in which other people can disagree productively. Sometimes my job is not to have the answer first, but to make sure the team can find a better one together.

    """

    summary = summarize_essay(test_prompt, test_response)

    print(summary)