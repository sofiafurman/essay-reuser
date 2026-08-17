from flask import Flask, request, redirect


from database import (
    init_db, save_essays, get_essays, save_chunks,
    save_prompt, get_prompts, get_chunks, save_analysis,
    get_analyses, get_prompt, get_analysis_details
)

from ai import (
    create_embedding, split_essay, create_embeddings,
    rank_chunks, analyze_matches
)
app = Flask(__name__)

init_db()

@app.route("/")
def home():
    return """
        <h1>Essay Reuser</h1>
        
        <form method="POST" action="/essays">
            <label>Application</label><br>
            <input name=application required><br><br>

            <label>Prompt</label><br>
            <textarea name=prompt required></textarea><br><br>

            <label>Response</label><br>
            <textarea name="response" rows="10" cols="60"></textarea>

            <button type="submit">Save Essay</button>
        </form>

        <hr>

        <h2>Add New Prompt</h2>

        <form method="POST" action="/prompts">
            <label>Application</label><br>
            <input name="application" required><br><br>

            <label>Prompt</label><br>
            <textarea name="prompt" required></textarea><br><br>

            <button type="submit">Analyze Prompt</button>
        </form>
    
    """

@app.route("/essays", methods=["GET"])
def view_essays():
    essays = get_essays()

    html = "<h1>My Library</h1>"

    for essay in essays:
        essay_id, application, prompt, response, embedding = essay

        html += f"""
            <hr>
            <p><strong>Application:</strong> {application}</p>
            <p><strong>Prompt:</strong> {prompt}</p>
            <p><strong>Response:</strong> {response}</p>
        """
    return html

@app.route("/essays", methods=["POST"])
def create_essay():
    application = request.form["application"]
    prompt = request.form["prompt"]
    response = request.form["response"]
    
    embedding = create_embedding(response) #whole essay

    essay_id = save_essays(application, prompt, response, embedding)

    chunks = split_essay(response)
    chunk_embeddings = create_embeddings(chunks)
    save_chunks(essay_id, chunks, chunk_embeddings)

    return "Essay saved!"

@app.route("/prompts", methods=["POST"])
def create_prompt():
    application = request.form["application"]
    prompt = request.form["prompt"]
    
    embedding = create_embedding(prompt) 
    prompt_id = save_prompt(application, prompt, embedding)

    chunks = get_chunks()
    ranked_chunks = rank_chunks(embedding, chunks)
    
    analysis = analyze_matches(prompt, ranked_chunks)

    save_analysis(prompt_id, analysis)
    return redirect(f"/prompts/{prompt_id}")

@app.route("/prompts", methods=["GET"])
def view_prompt_analyses():
    prompts = get_prompts()


    html = "<h1>My Prompt Analyses</h1>"

    for prompt in prompts:
        prompt_id, application, prompt_text, embedding_json = prompt

        analyses = get_analyses(prompt_id)

        html += f"""
            <hr>
            <p><strong>Application:</strong> {application}</p>
            <p><strong>Prompt:</strong> {prompt_text}</p>
            
        """

        for analysis in analyses:
            essay_id, chunk_index, classification, reason, adaptation_needed = analysis
            html += f"""
                <p>
                    <strong>{classification}</strong><br>
                    Essay {essay_id}, Chunk {chunk_index}<br>
                    {reason}<br>
                    <strong>Adaptation:</strong> {adaptation_needed}
                </p>
            """
    return html

@app.route("/prompts/<int:prompt_id>")
def view_prompt(prompt_id):
    prompt = get_prompt(prompt_id)

    if prompt is None:
        return 'Prompt not found', 404

    prompt_id, application, prompt_text = prompt

    analyses = get_analysis_details(prompt_id)

    html = f"""
    <h1>{application}</h1>
    <p><strong>Prompt:</strong> {prompt_text}</p>

    <h2>Reusable Writing</h2>
"""

    for analysis in analyses:
        (
            classification,
            reason,
            adaptation_needed,
            source_application,
            source_prompt,
            chunk_text
        ) = analysis

        html += f"""
            <hr>

            <h3>{source_application}</h3>

            <p><strong>{classification}</strong></p>

            <p><strong>Original prompt:</strong> {source_prompt}</p>

            <blockquote>{chunk_text}</blockquote>

            <p><strong>Why it matches:</strong> {reason}</p>

            <p><strong>How to adapt it:</strong> {adaptation_needed}</p>
        """
    return html

    
    

if __name__ == "__main__":
    app.run(debug=True)