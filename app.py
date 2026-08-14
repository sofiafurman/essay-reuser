from flask import Flask, request
from database import init_db, save_essays, get_essays
from ai import create_embedding

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
    
    embedding = create_embedding(response)

    save_essays(application, prompt, response, embedding)

    return "Essay saved!"

if __name__ == "__main__":
    app.run(debug=True)