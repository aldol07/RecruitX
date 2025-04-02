# RecruitX - AI Hiring Assistant

## Project Overview
RecruitX is an AI-powered Hiring Assistant that streamlines the candidate screening process. It collects candidate details, generates technical interview questions based on the provided tech stack, and evaluates responses. The chatbot is designed to enhance the efficiency of the hiring process by automating initial screenings and providing structured feedback.

## Installation Instructions

### Prerequisites
- Python 3.8+
- Virtual Environment (recommended)
- Required dependencies (listed in `requirements.txt`)

### Steps to Set Up Locally
1. **Clone the Repository**
   ```sh
   git clone https://github.com/aldol07/RecruitX.git
   cd RecruitX
   ```
2. **Create a Virtual Environment**
   ```sh
   python -m venv recruitx_env
   source recruitx_env/bin/activate  # On Windows use `recruitx_env\Scripts\activate`
   ```
3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set Up Environment Variables**
   - Create a `.env` file in the project root directory.
   - Add necessary API keys and configuration variables.

5. **Run the Application**
   ```sh
   python app.py
   ```

## Usage Guide
- Run `app.py` to start the chatbot.
- The chatbot will ask for candidate details.
- It will generate technical questions based on the provided tech stack.
- Responses are analyzed and saved in `candidate_details.json`.

## Technical Details
- **Backend:** Python (Flask)
- **Libraries:**
  - `ollama` (for AI-powered question generation and response analysis)
  - `textblob` (sentiment analysis)
  - `pdfplumber`, `python-docx` (resume text extraction)
- **Data Handling:** JSON file storage for candidate interactions

## Prompt Design
- **Greeting & Information Gathering:**
  - The chatbot starts with a friendly greeting and asks for candidate details.
- **Technical Question Generation:**
  - Uses a predefined prompt format to generate relevant interview questions.
- **Response Analysis:**
  - Evaluates sentiment, hesitation, and relevance.

## Challenges & Solutions
- **Challenge:** Ensuring the AI generates domain-specific technical questions.
  - **Solution:** Fine-tuned prompt engineering to optimize question generation.
- **Challenge:** Handling unstructured resume data.
  - **Solution:** Used `pdfplumber` and `python-docx` for text extraction and LLM-based parsing.

## Code Quality
### Structure & Readability
- Modular structure (`utils.py` for helper functions, `prompts.py` for prompt design).
- Follows best coding practices and is well-commented.

### Documentation
- Each function includes docstrings for clarity.
- `README.md` serves as a comprehensive guide.

### Version Control
- Git is used for version control.
- Clear commit messages and structured repository organization.

