import streamlit as st
import json
import os
from utils import generate_technical_questions, analyze_response, extract_tech_stack

# Path to JSON file
DATA_FILE = "candidate_details.json"

def load_data():
    """Load existing candidate data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data  # Ensure it's a list
                else:
                    return [data]  # Convert single entry to a list
            except json.JSONDecodeError:
                return []  # Return empty list if JSON is corrupted
    return []

def save_data():
    """Save session state data to JSON file."""
    candidates = load_data()
    candidates.append({
        "user_data": st.session_state.user_data,
        "responses": st.session_state.responses
    })
    with open(DATA_FILE, "w") as f:
        json.dump(candidates, f, indent=4)

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

st.set_page_config(page_title="RecruitX - AI Hiring Assistant", layout="centered")
st.title("RecruitX - AI Hiring Assistant")

# Reset button
def reset_chatbot():
    st.session_state.user_data = {}
    st.session_state.questions = []
    st.session_state.current_question_index = 0
    st.session_state.responses = []
    st.session_state.skipped_questions = []
    st.session_state.interview_complete = False
    st.rerun()

# UI for user details
if not st.session_state.user_data:
    st.subheader("Please enter your details to begin the interview")
    with st.form("user_details_form"):
        name = st.text_input("Full Name", "")
        email = st.text_input("Email Address", "")
        phone = st.text_input("Phone Number", "")
        experience = st.number_input("Years of Experience", min_value=0, step=1)
        position = st.text_input("Desired Position(s)", "")
        location = st.text_input("Current Location", "")
        tech_stack = st.text_area("Enter your tech stack (comma-separated)", "")
        uploaded_file = st.file_uploader("Upload Resume (Optional)", type=["pdf", "doc", "docx"])
        
        submit_button = st.form_submit_button("Start Interview")
        
        if submit_button:
            if uploaded_file:
                tech_stack_from_resume = extract_tech_stack(uploaded_file)
                tech_stack += ", " + tech_stack_from_resume if tech_stack else tech_stack_from_resume
            
            st.session_state.user_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "experience": experience,
                "position": position,
                "location": location,
                "tech_stack": tech_stack.split(", ")
            }
            st.session_state.questions = generate_technical_questions(st.session_state.user_data["tech_stack"])
            st.rerun()

# Chatbot UI
else:
    st.subheader(f"Hello {st.session_state['user_data']['name']}, let's begin your interview!")
    
    if st.session_state.current_question_index < len(st.session_state.questions):
        question = st.session_state.questions[st.session_state.current_question_index]
        st.write(f"Q{st.session_state.current_question_index + 1}: {question}")
        response = st.text_area("Your Answer:", key=f"response_{st.session_state.current_question_index}")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_ans = st.button("Submit")
        with col2:
            skip_ans = st.button("Skip")
        
        if submit_ans:
            if response.strip():
                feedback = analyze_response(response, question)
                st.session_state.responses.append({
                    "question": question,
                    "answer": response,
                    "feedback": feedback["feedback"]
                })
                st.session_state.current_question_index += 1
                st.rerun()
        
        if skip_ans:
            st.session_state.skipped_questions.append(question)
            st.session_state.responses.append({
                "question": question,
                "answer": "Skipped",
                "feedback": "No response provided."
            })
            st.session_state.current_question_index += 1
            st.rerun()
    
    else:
        st.subheader("Interview Summary")
        for i, entry in enumerate(st.session_state.responses):
            st.write(f"Q{i+1}: {entry['question']}")
            st.write(f"Your Answer: {entry['answer']}")
            st.write(f"Feedback: {entry['feedback']}")
            st.write("---")
        
        st.success("Interview Complete! Your responses have been saved for HR review.")
        save_data()
    
    st.button("Reset Interview", on_click=reset_chatbot)
