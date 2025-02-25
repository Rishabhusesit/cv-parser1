from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pdfplumber
import spacy
from langdetect import detect
from transformers import pipeline
import openai
import psycopg2
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load Sentence Transformer model for AI-based comparison
model = SentenceTransformer('all-MiniLM-L6-v2')

# Set upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection
# conn = psycopg2.connect(database="recruitment_db", user="postgres", password="password", host="localhost", port="5432")
# cursor = conn.cursor()

@app.route("/upload", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Extract text from PDF
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Detect language
    language = detect(text)

    # Process with spaCy
    doc = nlp(text)
    extracted_info = {
        "name": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
        "skills": [token.text for token in doc if token.pos_ == "NOUN"],
        "experience": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
    }

    return jsonify({
        "filename": file.filename,
        "language": language,
        "extracted_info": extracted_info
    })

@app.route("/compare", methods=["POST"])
def compare_resume_with_jd():
    data = request.json
    resume_text = data.get("resume_text", "")
    jd_text = data.get("jd_text", "")

    if not resume_text or not jd_text:
        return jsonify({"error": "Missing resume or job description"}), 400

    # Convert JD and Resume to embeddings
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    jd_embedding = model.encode(jd_text, convert_to_tensor=True)

    # Compute similarity score
    similarity_score = util.pytorch_cos_sim(resume_embedding, jd_embedding).item()

    return jsonify({"similarity_score": similarity_score})

@app.route("/store_results", methods=["POST"])
def store_results():
    data = request.json
    filename = data.get("filename")
    score = data.get("score")

    if not filename or score is None:
        return jsonify({"error": "Missing filename or score"}), 400

    cursor.execute("INSERT INTO results (filename, score) VALUES (%s, %s)", (filename, score))
    conn.commit()

    return jsonify({"message": "Stored successfully"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)

    import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT version();")
print(cur.fetchone())

conn.close()

import psycopg2

try:
    conn = psycopg2.connect(
        database="recruitment_db",
        user="postgres",
        password="Rishabh@05",
        host="localhost",
        port="5432"
    )
    print("Connection successful!")
except psycopg2.OperationalError as e:
    print(f"Connection failed: {e}")
