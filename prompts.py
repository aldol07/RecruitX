def get_greeting_prompt():
    return "Hello! I am RecruitX, your AI Hiring Assistant. Let's get started with your screening. Please provide your full name."

def get_info_prompt():
    return "Great! Now, please provide your email, phone number, years of experience, and desired position(s)."

def get_tech_stack_prompt():
    return "Now, tell me about your technical skills. List the programming languages, frameworks, databases, and tools you are proficient in."

def get_question_generation_prompt(tech_stack):
    return f"Generate at least 5 technical interview questions for a candidate skilled in {tech_stack}."

def get_closing_prompt():
    return "Thank you for your responses! We will review your answers and get back to you soon. Have a great day!"
