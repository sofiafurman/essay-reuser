from flask import Flask, request, redirect


from database import (
    init_db, save_essays, get_essays, save_chunks,
    save_prompt, get_prompts, get_chunks, save_analysis,
    get_prompt, get_essay_analysis_details, get_chunk_analysis_details,
    get_essay, delete_essay
)

from ai import (
    create_embedding, split_essay, create_embeddings,
    rank_chunks, analyze_matches, rank_essays
)
app = Flask(__name__)

init_db()

@app.route("/")
def home():

    return """
        <nav>
            <a href="/">Home</a> |
            <a href="/essays">Essay Library</a> |
            <a href="/prompts">Prompt Library</a>
        </nav>

        <hr>

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

    html = """
        <nav>
            <a href="/">Home</a> |
            <a href="/essays">Essay Library</a> |
            <a href="/prompts">Prompt Library</a>
        </nav>

        <hr>

        <h1>Essay Library</h1>
    """

    for essay in essays:
        essay_id, application, prompt, response, embedding = essay

        html += f"""
            <hr>
            <p><strong>Application:</strong> {application}</p>
            <p><strong>Prompt:</strong> {prompt}</p>
            <p><strong>Response:</strong> {response}</p>
            <a href="/essays/{essay_id}">View Essay Page</a>
        """
    return html

@app.route("/essays/<int:essay_id>")
def view_essay(essay_id):
    essay = get_essay(essay_id)

    if essay is None:
        return "Essay not found", 404

    essay_id, application, prompt_text, response = essay
    

    html = """
            <nav>
                <a href="/">Home</a> |
                <a href="/essays">Essay Library</a> |
                <a href="/prompts">Prompt Library</a>
            </nav>
    
            <hr>
        """
    
    html += f"""
        <h1>{application}</h1>
        <p><strong>Prompt:</strong> {prompt_text}</p>

        <p>{response}</p>
    """

    html += f"""
    <form method="POST" action="/essays/{essay_id}/delete">
        <button type="submit">[Delete Essay]</button>
    </form>
    """

    html += f"""
    <p><a href="/essays/{essay_id}/edit">Edit Essay</a></p>
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

    return redirect(f"/essays/{essay_id}")  

@app.route("/essays/<int:essay_id>/delete", methods=["POST"])
def delete_essay_route(essay_id):
    delete_essay(essay_id)

    return redirect("/essays")

@app.route("/essays/<int:essay_id>/edit", methods=["GET"])
def edit_essay_route(essay_id):
    essay = get_essay(essay_id)

    if essay is None:
        return "Essay not found", 404

    essay_id, application, prompt_text, response = essay

    html = f"""
        <nav>
            <a href="/">Home</a> |
            <a href="/essays">Essay Library</a> |
            <a href="/prompts">Prompt Library</a>
        </nav>

        <hr>

        <h1>Edit Essay</h1>

        <form method="POST" action="/essays/{essay_id}/edit">

            <label>Application</label><br>
            <input
                name="application"
                value="{application}"
                required
            ><br><br>

            <label>Prompt</label><br>
            <textarea name="prompt" required>{prompt_text}</textarea>
            <br><br>

            <label>Response</label><br>
            <textarea
                name="response"
                rows="15"
                cols="70"
                required
            >{response}</textarea>
            <br><br>

            <button type="submit">Save Changes</button>
        </form>
    """

    return html

@app.route("/prompts", methods=["POST"])
def create_prompt():
    application = request.form["application"]
    prompt = request.form["prompt"]
    
    embedding = create_embedding(prompt) 
    prompt_id = save_prompt(application, prompt, embedding)

    chunks = get_chunks()
    essays = get_essays()

    ranked_essays = rank_essays(embedding, essays)
    ranked_chunks = rank_chunks(embedding, chunks)

    #debugging start
    print("\nWHOLE ESSAYS")
    for essay in ranked_essays:
        print(
            essay["application"],
            round(essay["similarity_score"], 3)
        )

    print("\nCHUNKS")
    for chunk in ranked_chunks[:5]:
        print(
            "Essay", chunk["essay_id"],
            "Chunk", chunk["chunk_index"],
            round(chunk["similarity_score"], 3)
        )
    #debugging end
    
    analysis = analyze_matches(
    prompt,
    ranked_essays,
    ranked_chunks
)

    save_analysis(prompt_id, analysis)

    print("\nESSAY RECOMMENDATIONS")

    for match in analysis.essay_matches:
        print(
            match.essay_id,
            match.classification,
            match.reason
        )

    print("\nPASSAGE RECOMMENDATIONS")

    for match in analysis.chunk_matches:
        print(
            match.essay_id,
            match.chunk_index,
            match.classification,
            match.reason
        )

    return redirect(f"/prompts/{prompt_id}")  

@app.route("/prompts", methods=["GET"])
def view_prompts():
    prompts = get_prompts()

    html = """
        <nav>
            <a href="/">Home</a> |
            <a href="/essays">Essay Library</a> |
            <a href="/prompts">Prompt Library</a>
        </nav>

        <hr>

        <h1>Prompt Library</h1>
    """

    for prompt in prompts:
        prompt_id, application, prompt_text, embedding_json = prompt

        html += f"""
            <hr>

            <h3>{application}</h3>

            <p>{prompt_text}</p>

            <a href="/prompts/{prompt_id}">View Analysis</a>
        """

    return html

@app.route("/prompts/<int:prompt_id>")
def view_prompt(prompt_id):
    prompt = get_prompt(prompt_id)

    if prompt is None:
        return "Prompt not found", 404

    prompt_id, application, prompt_text = prompt

    essay_analyses = get_essay_analysis_details(prompt_id)

    html = """
            <nav>
                <a href="/">Home</a> |
                <a href="/essays">Essay Library</a> |
                <a href="/prompts">Prompt Library</a>
            </nav>
    
            <hr>
        """
    html += f"""
        <h1>{application}</h1>
        <p><strong>Prompt:</strong> {prompt_text}</p>

        <h2>Reusable Writing</h2>
    """

    for essay_analysis in essay_analyses:
        (
            essay_id,
            classification,
            reason,
            adaptation_needed,
            source_application,
            source_prompt,
            source_response
        ) = essay_analysis

        html += f"""
        <hr>

        <h3>{source_application}</h3>

        <p><strong>Original prompt:</strong> {source_prompt}</p>
    """

        if classification:
            html += f"""
                <p><strong>Whole Essay: {classification}</strong></p>

                <p><strong>Why this essay matches:</strong> {reason}</p>
            """

            if adaptation_needed:
                html += f"""
                    <p>
                        <strong>How to adapt the essay:</strong>
                        {adaptation_needed}
                    </p>
                """

        html += """
            <h4>Relevant Passages</h4>
        """

        chunk_analyses = get_chunk_analysis_details(
            prompt_id,
            essay_id
        )

        for chunk_analysis in chunk_analyses:
            (
                chunk_index,
                chunk_classification,
                chunk_reason,
                chunk_adaptation,
                chunk_text
            ) = chunk_analysis

            html += f"""
                <blockquote>{chunk_text}</blockquote>

                <p><strong>{chunk_classification}</strong></p>

                <p>
                    <strong>Why this passage:</strong>
                    {chunk_reason}
                </p>
            """

            if chunk_adaptation:
                html += f"""
                    <p>
                        <strong>How to adapt:</strong>
                        {chunk_adaptation}
                    </p>
                """

    return html

if __name__ == "__main__":
    app.run(debug=True)