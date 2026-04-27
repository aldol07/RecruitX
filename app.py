import streamlit as st
import json
import os
import html
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from utils import generate_technical_questions, analyze_response, extract_tech_stack

# Path to JSON file
DATA_FILE = "candidate_details.json"
LOG_FILE = "recruitx.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("recruitx")

def load_data():
    """Load existing candidate data from JSON file."""
    logger.info("Loading candidate data from %s", DATA_FILE)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data  # Ensure it's a list
                else:
                    return [data]  # Convert single entry to a list
            except json.JSONDecodeError:
                logger.exception("Candidate data file is corrupted; returning empty data")
                return []  # Return empty list if JSON is corrupted
    return []

def save_data():
    """Save session state data to JSON file."""
    if st.session_state.get("saved"):
        logger.info("Skipping save because current interview is already saved")
        return

    logger.info("Saving interview responses count=%s", len(st.session_state.responses))
    candidates = load_data()
    candidates.append({
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "user_data": st.session_state.user_data,
        "responses": st.session_state.responses
    })
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=4)
    st.session_state.saved = True
    logger.info("Interview saved total_candidates=%s", len(candidates))


def parse_tech_stack(value):
    """Normalize comma or newline separated technology input."""
    return [
        item.strip()
        for item in value.replace("\n", ",").split(",")
        if item.strip()
    ]


def safe_text(value):
    """Escape user and AI text before rendering inside custom HTML cards."""
    return html.escape(str(value))


def generate_interview_reviews(responses, user_data):
    """Evaluate completed answers in parallel to reduce final review wait time."""
    review_jobs = {}
    reviewed_responses = list(responses)

    with ThreadPoolExecutor(max_workers=min(5, max(1, len(reviewed_responses)))) as executor:
        for index, entry in enumerate(reviewed_responses):
            if entry["answer"] == "Skipped":
                logger.info("Skipping review generation for skipped question")
                continue

            logger.info(
                "Queueing review for question_index=%s question_chars=%s answer_chars=%s",
                index,
                len(entry["question"]),
                len(entry["answer"]),
            )
            future = executor.submit(analyze_response, entry["answer"], entry["question"], user_data)
            review_jobs[future] = index

        for future in as_completed(review_jobs):
            index = review_jobs[future]
            feedback = future.result()
            reviewed_responses[index]["feedback"] = feedback.get("feedback", "Feedback generated.")
            reviewed_responses[index]["score"] = feedback.get("score")
            reviewed_responses[index]["strengths"] = feedback.get("strengths")
            reviewed_responses[index]["improvements"] = feedback.get("improvements")
            reviewed_responses[index]["recommendation"] = feedback.get("recommendation")
            logger.info("Review completed for question_index=%s", index)

    return reviewed_responses

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'interview_complete' not in st.session_state:
    st.session_state.interview_complete = False
if 'skipped_questions' not in st.session_state:
    st.session_state.skipped_questions = []
if 'saved' not in st.session_state:
    st.session_state.saved = False
if 'review_ready' not in st.session_state:
    st.session_state.review_ready = False

st.set_page_config(page_title="RecruitX - AI Hiring Assistant", layout="centered")

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(79, 70, 229, 0.18), transparent 28rem),
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 26rem),
                linear-gradient(135deg, #f8fbff 0%, #eef4ff 45%, #fbfdff 100%);
            color: #0f172a;
        }
        .main .block-container {
            max-width: 1040px;
            padding-top: 2rem;
            padding-bottom: 3rem;
            color: #0f172a;
        }
        .hero {
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(49, 46, 129, 0.92)),
                linear-gradient(135deg, #1f4fd8 0%, #6d5dfc 100%);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 30px;
            color: white;
            padding: 2.15rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 24px 70px rgba(30, 41, 59, 0.22);
        }
        .hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 2.65rem;
            line-height: 1.1;
            letter-spacing: -0.04em;
        }
        .hero p {
            margin: 0;
            color: rgba(255, 255, 255, 0.86);
            font-size: 1.05rem;
            max-width: 720px;
        }
        .eyebrow {
            color: #c7d2fe;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            margin-bottom: 0.65rem;
            text-transform: uppercase;
        }
        .stats {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 1.2rem 0 1.45rem;
        }
        .stat {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 18px;
            box-shadow: 0 12px 26px rgba(15, 23, 42, 0.07);
            color: #0f172a;
            padding: 1rem;
        }
        .stat strong {
            color: #1d4ed8;
            display: block;
            font-size: 1.35rem;
            line-height: 1;
        }
        .stat span {
            color: #64748b;
            font-size: 0.88rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 24px;
            color: #0f172a;
            padding: 1.45rem;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }
        .card h3,
        .card h4,
        .card p,
        .card strong {
            color: #0f172a;
        }
        .question-card {
            border-left: 6px solid #4f46e5;
        }
        .muted {
            color: #64748b;
            font-size: 0.95rem;
        }
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 24px;
            color: #0f172a;
            padding: 1.35rem;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
        }
        div[data-testid="stForm"] label,
        div[data-testid="stForm"] p,
        div[data-testid="stForm"] span {
            color: #0f172a;
        }
        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 999px;
            border: 0;
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            font-weight: 700;
            padding: 0.7rem 1.25rem;
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            color: white;
            filter: brightness(1.03);
        }
        @media (max-width: 760px) {
            .stats {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: 2.15rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">AI Hiring Assistant</div>
        <h1>RecruitX</h1>
        <p>Run crisp first-round technical screenings with tailored questions, smooth answer capture, and a clean final review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="stats">
        <div class="stat"><strong>5</strong><span>Focused questions</span></div>
        <div class="stat"><strong>AI</strong><span>Structured feedback</span></div>
        <div class="stat"><strong>1</strong><span>Clean interview review</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Reset button
def reset_chatbot():
    logger.info("Resetting interview session state")
    st.session_state.user_data = {}
    st.session_state.questions = []
    st.session_state.current_question_index = 0
    st.session_state.responses = []
    st.session_state.skipped_questions = []
    st.session_state.interview_complete = False
    st.session_state.saved = False
    st.session_state.review_ready = False
    st.rerun()

# UI for user details
if not st.session_state.user_data:
    st.markdown("### Candidate Details")
    st.markdown('<p class="muted">Fill in the profile below. Resume upload is optional and helps enrich the tech stack.</p>', unsafe_allow_html=True)
    with st.form("user_details_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", "")
            email = st.text_input("Email Address", "")
            experience = st.number_input("Years of Experience", min_value=0, step=1)
        with col2:
            phone = st.text_input("Phone Number", "")
            position = st.text_input("Desired Position(s)", "")
            location = st.text_input("Current Location", "")

        tech_stack = st.text_area("Enter your tech stack (comma-separated)", "")
        uploaded_file = st.file_uploader("Upload Resume (Optional)", type=["pdf", "doc", "docx"])
        
        submit_button = st.form_submit_button("Start Interview")
        
        if submit_button:
            logger.info(
                "Start Interview clicked has_resume=%s position=%s experience=%s",
                bool(uploaded_file),
                position or "Not specified",
                experience,
            )
            if not name or not email or not position:
                logger.warning("Candidate form validation failed missing_required_fields=True")
                st.error("Please provide at least your name, email, and desired position.")
                st.stop()

            with st.spinner("Preparing your personalized interview..."):
                if uploaded_file:
                    try:
                        tech_stack_from_resume = extract_tech_stack(uploaded_file)
                        tech_stack += ", " + tech_stack_from_resume if tech_stack else tech_stack_from_resume
                    except Exception as exc:
                        logger.exception("Resume parsing failed: %s", exc)
                        st.warning(f"Resume parsing could not be completed: {exc}")

                parsed_stack = parse_tech_stack(tech_stack)
                logger.info("Candidate tech stack parsed count=%s", len(parsed_stack))
            
            st.session_state.user_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "experience": experience,
                "position": position,
                "location": location,
                "tech_stack": parsed_stack
            }

            try:
                with st.spinner("Loading your first interview question..."):
                    st.session_state.questions = generate_technical_questions(
                        st.session_state.user_data["tech_stack"],
                        position=position,
                        experience=experience,
                    )
                    if not st.session_state.questions:
                        raise RuntimeError("No interview questions were generated. Please try again.")
                    logger.info("Questions loaded into session count=%s", len(st.session_state.questions))
            except Exception as exc:
                st.session_state.user_data = {}
                logger.exception("Could not start interview: %s", exc)
                st.error(f"Could not generate questions: {exc}")
                st.stop()

            st.session_state.current_question_index = 0
            st.session_state.responses = []
            st.session_state.interview_complete = False
            st.session_state.review_ready = False
            st.session_state.saved = False
            st.rerun()

# Chatbot UI
else:
    user_data = st.session_state["user_data"]
    if not st.session_state.questions:
        logger.error("Interview session has user_data but no questions")
        st.error("No interview questions were found for this session. Please restart and try again.")
        st.button("Back to Candidate Form", on_click=reset_chatbot)
        st.stop()

    st.markdown(f"### Hello {safe_text(user_data['name'])}, let's begin your interview.")
    st.markdown(
        f'<div class="card"><strong>Role:</strong> {safe_text(user_data["position"])}<br>'
        f'<strong>Experience:</strong> {safe_text(user_data["experience"])} years<br>'
        f'<strong>Tech Stack:</strong> {safe_text(", ".join(user_data["tech_stack"]) or "Not provided")}</div>',
        unsafe_allow_html=True,
    )
    
    if st.session_state.current_question_index < len(st.session_state.questions):
        total_questions = len(st.session_state.questions)
        progress = st.session_state.current_question_index / total_questions if total_questions else 0
        st.progress(progress)

        question = st.session_state.questions[st.session_state.current_question_index]
        st.markdown(
            f'<div class="card question-card"><span class="muted">Question '
            f'{st.session_state.current_question_index + 1} of {total_questions}</span>'
            f'<h3>{safe_text(question)}</h3></div>',
            unsafe_allow_html=True,
        )
        response = st.text_area("Your Answer:", key=f"response_{st.session_state.current_question_index}")
        
        col1, col2 = st.columns(2)
        with col1:
            next_ans = st.button("Next")
        with col2:
            skip_ans = st.button("Skip")
        
        if next_ans:
            if response.strip():
                logger.info(
                    "Answer recorded question_index=%s answer_chars=%s",
                    st.session_state.current_question_index,
                    len(response),
                )
                st.session_state.responses.append({
                    "question": question,
                    "answer": response,
                    "feedback": "Pending review.",
                    "score": None,
                    "strengths": "",
                    "improvements": "",
                    "recommendation": "Pending",
                })
                st.session_state.current_question_index += 1
                if st.session_state.current_question_index >= len(st.session_state.questions):
                    st.session_state.interview_complete = True
                    logger.info("All interview questions answered responses=%s", len(st.session_state.responses))
                st.rerun()
            else:
                logger.warning("Next clicked with empty answer question_index=%s", st.session_state.current_question_index)
                st.warning("Please write an answer or skip the question.")
        
        if skip_ans:
            logger.info("Question skipped question_index=%s", st.session_state.current_question_index)
            st.session_state.skipped_questions.append(question)
            st.session_state.responses.append({
                "question": question,
                "answer": "Skipped",
                "feedback": "No response provided.",
                "score": 0,
                "strengths": "",
                "improvements": "Candidate skipped this question.",
                "recommendation": "Needs Review",
            })
            st.session_state.current_question_index += 1
            if st.session_state.current_question_index >= len(st.session_state.questions):
                st.session_state.interview_complete = True
                logger.info("All interview questions completed with skip responses=%s", len(st.session_state.responses))
            st.rerun()
    
    else:
        st.progress(1.0)
        if not st.session_state.review_ready:
            st.markdown("### All questions answered")
            st.markdown(
                '<div class="card"><p>Your answers are ready. Click <strong>Save Interview</strong> to generate the final review and save the interview. Reviews are processed together to reduce waiting time.</p></div>',
                unsafe_allow_html=True,
            )

            if st.button("Save Interview"):
                logger.info("Save Interview clicked responses=%s", len(st.session_state.responses))
                with st.spinner("Generating final review..."):
                    st.session_state.responses = generate_interview_reviews(
                        st.session_state.responses,
                        user_data,
                    )
                    save_data()
                    st.session_state.review_ready = True
                    logger.info("Interview review generated and marked ready")
                st.rerun()
        else:
            st.subheader("Interview Review")
            for i, entry in enumerate(st.session_state.responses):
                st.markdown(
                    f'<div class="card"><span class="muted">Question {i + 1}</span>'
                    f'<h4>{safe_text(entry["question"])}</h4>'
                    f'<p><strong>Answer:</strong> {safe_text(entry["answer"])}</p>'
                    f'<p><strong>Feedback:</strong> {safe_text(entry["feedback"])}</p>'
                    f'<p><strong>Score:</strong> {safe_text(entry.get("score", "N/A"))} / 10</p>'
                    f'<p><strong>Recommendation:</strong> {safe_text(entry.get("recommendation", "N/A"))}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.success("Interview saved. Review is ready for HR.")
    
    st.button("Reset Interview", on_click=reset_chatbot)
