import json
import os
import random
import pdfplumber
import ollama
from docx import Document
from textblob import TextBlob

def save_interaction(user_input, bot_reply, sentiment, hesitation, feedback):
    """Save conversation interactions to a JSON file."""
    interaction = {
        "user_input": user_input,
        "bot_reply": bot_reply,
        "sentiment": sentiment,
        "hesitation": hesitation,
        "feedback": feedback
    }
    
    if os.path.exists("interactions.json"):
        with open("interactions.json", "r") as f:
            data = json.load(f)
    else:
        data = []
    
    data.append(interaction)
    
    with open("interactions.json", "w") as f:
        json.dump(data, f, indent=4)

def analyze_response(response, question):
    """Analyze the chatbot's response based on sentiment, hesitation, and relevance to the question."""
    sentiment_score = TextBlob(response).sentiment.polarity
    hesitation_keywords = ["maybe", "I think", "possibly", "not sure", "could be"]
    hesitation_score = sum([response.lower().count(word) for word in hesitation_keywords])
    
    sentiment = "Positive" if sentiment_score > 0 else "Neutral" if sentiment_score == 0 else "Negative"
    hesitation = "High" if hesitation_score > 2 else "Moderate" if hesitation_score > 0 else "Low"
    
    # Basic relevance check (you can improve this logic)
    relevance = "Relevant" if any(word in response.lower() for word in question.lower().split()) else "Possibly Irrelevant"
    
    feedback = "The response was well-structured and confident." if hesitation == "Low" else "Consider refining the response for clarity and confidence."
    
    return {"sentiment": sentiment, "hesitation": hesitation, "relevance": relevance, "feedback": feedback}


def generate_technical_questions(tech_stack):
    """Generate at least 5 relevant technical interview questions based on the declared tech stack using Mistral LLM."""
    prompt = f"Generate 5 technical interview questions for a candidate skilled in {tech_stack}."
    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )
    
    questions = response["message"]["content"].split("\n")
    return [q for q in questions if q.strip()][:5]

def extract_text_from_pdf(file):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file):
    """Extract text from a DOCX file."""
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_tech_stack(uploaded_file):
    """Extract technology stack from a resume file (PDF or DOCX)."""
    if uploaded_file is None:
        return ""
    
    file_extension = uploaded_file.name.split(".")[-1].lower()
    
    if file_extension == "pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_extension in ["doc", "docx"]:
        resume_text = extract_text_from_docx(uploaded_file)
    else:
        return ""
    
    # Use an LLM to extract tech stack from the text
    prompt = f"Extract and list the technical skills, programming languages, frameworks, and tools from this resume: {resume_text[:1000]}..."
    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tech_stack = response["message"]["content"].split(",")
    return ", ".join([tech.strip() for tech in tech_stack if tech.strip()])
