from utils import save_interaction, analyze_response, generate_technical_questions
from prompts import get_greeting_prompt, get_info_prompt, get_tech_stack_prompt, get_closing_prompt

def chat_with_candidate():
    """Main chatbot function to interact with candidates."""
    print(get_greeting_prompt())
    user_name = input("Name: ")
    
    print(get_info_prompt())
    email = input("Email: ")
    phone = input("Phone: ")
    experience = input("Years of Experience: ")
    position = input("Desired Position(s): ")
    
    print(get_tech_stack_prompt())
    tech_stack = input("Tech Stack: ")
    
    questions = generate_technical_questions(tech_stack, position=position, experience=experience)
    print("Here are your technical questions:")
    for i, question in enumerate(questions, 1):
        print(f"{i}. {question}")
    
    print(get_closing_prompt())
    
    analysis = analyze_response(" ".join(questions), "Generated screening questions")
    save_interaction(
        tech_stack,
        "\n".join(questions),
        analysis.get("sentiment"),
        analysis.get("hesitation"),
        analysis.get("feedback"),
    )
    
if __name__ == "__main__":
    chat_with_candidate()
