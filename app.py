from flask import(
    Flask, request, redirect,
    render_template
)

from database import (
    init_db, save_essays, get_essays, save_chunks,
    save_prompt, get_prompts, get_chunks, save_analysis,
    get_prompt, get_essay_analysis_details, get_chunk_analysis_details,
    get_essay, delete_essay, update_essay, delete_prompt
)

from ai import (
    create_embedding, split_essay, create_embeddings,
    rank_chunks, analyze_matches, rank_essays
)
app = Flask(__name__)

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/essays", methods=["GET"])
def view_essays():
    essays = get_essays()

    return render_template(
        "essays.html",
        essays=essays
    )

@app.route("/essays/<int:essay_id>")
def view_essay(essay_id):
    essay = get_essay(essay_id)

    if essay is None:
        return "Essay not found", 404

    return render_template(
        "essay.html",
        essay=essay
    )
    
@app.route("/essays", methods=["POST"])
def create_essay():
    application = request.form["application"].strip()
    prompt = request.form["prompt"].strip()
    response = request.form["response"].strip()

    if not application or not prompt or not response:
        return "Application, prompt, and response are required.", 400

    try:
        embedding = create_embedding(response) #whole essay

        chunks = split_essay(response)
        chunk_embeddings = create_embeddings(chunks)

    except Exception as error:
        print("Essay creation error:", error)
        return "We couldn't process this essay. Please try again.", 500

    essay_id = save_essays(application, prompt, response, embedding)
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

    return render_template(
        "edit_essay.html",
        essay=essay
    )

@app.route("/essays/<int:essay_id>/edit", methods=["POST"])
def edit_essay(essay_id):

    essay = get_essay(essay_id)

    if essay is None:
        return "Essay not found", 404

    application = request.form["application"].strip()
    prompt = request.form["prompt"].strip()
    response = request.form["response"].strip()

    if not application or not prompt or not response:
        return "Application, prompt, and response are required.", 400


    try:
        embedding = create_embedding(response)

        chunks = split_essay(response)
        chunk_embeddings = create_embeddings(chunks)

    except Exception as error:
            print("Essay editing error:", error)
            return "We couldn't process these changes. Please try again.", 500
    
    update_essay(
        essay_id,
        application,
        prompt,
        response,
        embedding,
        chunks,
        chunk_embeddings
    )

    return redirect(f"/essays/{essay_id}")

@app.route("/prompts", methods=["POST"])
def create_prompt():

    application = request.form["application"].strip()
    prompt = request.form["prompt"].strip()

    if not application or not prompt:
        return "Application and prompt are required.", 400
    
    essays = get_essays()
    
    if not essays:
            return "Add at least one essay before analyzing a prompt.", 400
    
    try:
        embedding = create_embedding(prompt) 

        chunks = get_chunks()

     
        ranked_essays = rank_essays(embedding, essays)
        ranked_chunks = rank_chunks(embedding, chunks)

        analysis = analyze_matches(
            prompt,
            ranked_essays,
            ranked_chunks
        )
        
        

    except Exception as error:
        print("Analysis error:", error)

        return """
            <h1>Something went wrong</h1>
            <p>We couldn't analyze this prompt. Please try again.</p>
            <a href="/">Back to Home</a>
        """, 500

    prompt_id = save_prompt(application, prompt, embedding)



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

    return render_template(
        "prompts.html",
        prompts=prompts
    )

@app.route("/prompts/<int:prompt_id>")
def view_prompt(prompt_id):
    prompt = get_prompt(prompt_id)

    if prompt is None:
        return "Prompt not found", 404

    essay_analyses = get_essay_analysis_details(prompt_id)

    results = []

    for essay_analysis in essay_analyses:
        essay_id = essay_analysis[0]

        chunk_analyses = get_chunk_analysis_details(
            prompt_id,
            essay_id
        )

        results.append({
            "essay": essay_analysis,
            "chunks": chunk_analyses
        })

    return render_template(
        "prompt.html",
        prompt=prompt,
        results=results
    )

@app.route("/prompts/<int:prompt_id>/delete", methods=["POST"])
def delete_prompt_route(prompt_id):
    prompt = get_prompt(prompt_id)

    if prompt is None:
        return "Prompt not found", 404

    delete_prompt(prompt_id)

    return redirect("/prompts")

if __name__ == "__main__":
    app.run(debug=True)