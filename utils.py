import json
import logging
import os
import re
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from textblob import TextBlob

load_dotenv()

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
logger = logging.getLogger("recruitx")


def get_setting(name, default=None):
    """Read config from environment variables or Streamlit Cloud secrets."""
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        return st.secrets.get(name, default)
    except Exception:
        return default


def _get_openrouter_client():
    """Create an OpenRouter client using the OpenAI-compatible API."""
    api_key = get_setting("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def call_ai(messages, temperature=0.3, max_tokens=1200):
    """Call DeepSeek R1 through OpenRouter and return the response text."""
    client = _get_openrouter_client()
    model = get_setting("OPENROUTER_MODEL", OPENROUTER_MODEL)
    logger.info("Calling OpenRouter model=%s max_tokens=%s", model, max_tokens)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_headers={
            "HTTP-Referer": get_setting("APP_URL", "http://localhost:8501"),
            "X-Title": "RecruitX",
        },
    )
    content = completion.choices[0].message.content.strip()
    logger.info("OpenRouter response received characters=%s", len(content))
    return content


def _extract_json_object(text):
    """Parse JSON from a model response, including responses wrapped in markdown."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _extract_json_array(text):
    """Parse a JSON array from model output."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _fallback_technical_questions(tech_stack, position="", experience=0):
    """Create usable screening questions if the model returns an empty response."""
    tech_stack_text = ", ".join(tech_stack) if isinstance(tech_stack, list) else str(tech_stack)
    focus = tech_stack_text or position or "your primary technology"
    try:
        years = int(experience or 0)
    except (TypeError, ValueError):
        years = 0
    level = "senior" if years >= 5 else "practical"

    return [
        f"Can you explain a recent {focus} project you worked on and the main technical decisions you made?",
        f"What are the most common performance issues you have seen while working with {focus}, and how did you solve them?",
        f"How would you debug a production issue in a {focus}-based application?",
        f"What testing approach would you use for a {level} feature built with {focus}?",
        f"Describe one challenging problem you solved using {focus} and what you learned from it.",
    ]


def save_interaction(user_input, bot_reply, sentiment, hesitation, feedback):
    """Save conversation interactions to a JSON file."""
    logger.info("Saving CLI interaction sentiment=%s hesitation=%s", sentiment, hesitation)
    interaction = {
        "user_input": user_input,
        "bot_reply": bot_reply,
        "sentiment": sentiment,
        "hesitation": hesitation,
        "feedback": feedback
    }
    
    if os.path.exists("interactions.json"):
        with open("interactions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    
    data.append(interaction)
    
    with open("interactions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    logger.info("CLI interaction saved total_records=%s", len(data))

def _fallback_response_analysis(response, question):
    """Return basic feedback when the AI evaluator is unavailable."""
    sentiment_score = TextBlob(response).sentiment.polarity
    hesitation_keywords = ["maybe", "I think", "possibly", "not sure", "could be"]
    hesitation_score = sum([response.lower().count(word) for word in hesitation_keywords])
    
    sentiment = "Positive" if sentiment_score > 0 else "Neutral" if sentiment_score == 0 else "Negative"
    hesitation = "High" if hesitation_score > 2 else "Moderate" if hesitation_score > 0 else "Low"
    
    # Basic relevance check (you can improve this logic)
    relevance = "Relevant" if any(word in response.lower() for word in question.lower().split()) else "Possibly Irrelevant"
    
    feedback = "The response was well-structured and confident." if hesitation == "Low" else "Consider refining the response for clarity and confidence."
    
    return {
        "sentiment": sentiment,
        "hesitation": hesitation,
        "relevance": relevance,
        "score": 6,
        "feedback": feedback,
        "strengths": "Basic response captured.",
        "improvements": "A deeper technical explanation would improve the answer.",
        "recommendation": "Needs Review",
    }


def analyze_response(response, question, candidate_context=None):
    """Evaluate a candidate answer with DeepSeek R1 and return structured feedback."""
    context = candidate_context or {}
    logger.info(
        "Starting response analysis question_chars=%s answer_chars=%s",
        len(question),
        len(response),
    )
    prompt = f"""
Evaluate this interview answer for a hiring screening tool.

Question:
{question}

Candidate answer:
{response}

Candidate context:
{json.dumps(context, indent=2)}

Return only valid JSON with these keys:
sentiment, hesitation, relevance, score, feedback, strengths, improvements, recommendation.

Rules:
- score must be an integer from 1 to 10.
- feedback must be concise and useful for the candidate.
- recommendation must be one of: Strong, Good, Average, Needs Review.
- Do not include hidden reasoning, markdown, or extra text.
"""
    try:
        result = call_ai(
            [
                {"role": "system", "content": "You are a precise technical interviewer and hiring evaluator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=550,
        )
        parsed = _extract_json_object(result)
        parsed.setdefault("feedback", "Feedback generated successfully.")
        parsed.setdefault("score", 0)
        logger.info(
            "Response analysis completed score=%s recommendation=%s",
            parsed.get("score"),
            parsed.get("recommendation"),
        )
        return parsed
    except Exception as exc:
        logger.exception("Response analysis failed, using fallback: %s", exc)
        return _fallback_response_analysis(response, question)


def generate_technical_questions(tech_stack, position="", experience=0):
    """Generate relevant technical interview questions for the candidate profile."""
    tech_stack_text = ", ".join(tech_stack) if isinstance(tech_stack, list) else str(tech_stack)
    logger.info(
        "Starting question generation position=%s experience=%s tech_count=%s",
        position or "Not specified",
        experience,
        len(tech_stack) if isinstance(tech_stack, list) else 1,
    )
    prompt = f"""
Generate 5 practical technical interview questions.

Candidate profile:
- Desired position: {position or "Not specified"}
- Years of experience: {experience}
- Tech stack: {tech_stack_text}

Return only a JSON array of 5 strings. Do not include markdown or numbering.
Questions should be specific, job-relevant, and suitable for a first screening round.
"""
    try:
        response = call_ai(
            [
                {"role": "system", "content": "You create focused technical screening questions for recruiters."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        max_tokens=650,
        )
    except Exception as exc:
        logger.exception("Question generation API call failed, using fallback: %s", exc)
        return _fallback_technical_questions(tech_stack, position, experience)

    try:
        questions = _extract_json_array(response)
    except Exception:
        questions = [
            re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
            for line in response.splitlines()
            if line.strip()
        ]

    cleaned_questions = [str(question).strip() for question in questions if str(question).strip()][:5]
    if cleaned_questions:
        logger.info("Question generation completed count=%s", len(cleaned_questions))
        return cleaned_questions

    logger.warning("Question generation returned no usable questions, using fallback")
    return _fallback_technical_questions(tech_stack, position, experience)

def extract_text_from_pdf(file):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
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
    logger.info("Starting resume tech extraction file_type=%s", file_extension)
    
    if file_extension == "pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_extension in ["doc", "docx"]:
        resume_text = extract_text_from_docx(uploaded_file)
    else:
        return ""
    
    prompt = f"""
Extract technical skills, programming languages, frameworks, databases, cloud tools, and developer tools from this resume text.

Resume text:
{resume_text[:4000]}

Return only a comma-separated list. Do not include explanations.
"""
    response = call_ai(
        [
            {"role": "system", "content": "You extract clean technology skill lists from resumes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=450,
    )

    tech_stack = response.replace("\n", ",").split(",")
    cleaned_stack = ", ".join([tech.strip() for tech in tech_stack if tech.strip()])
    logger.info("Resume tech extraction completed skill_count=%s", len([tech for tech in tech_stack if tech.strip()]))
    return cleaned_stack
