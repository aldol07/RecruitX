# RecruitX

RecruitX is an AI-powered hiring assistant built with Streamlit. It helps recruiters run a clean first-round technical screening by collecting candidate details, generating role-specific interview questions, capturing answers, and producing a structured interview review.

The app uses **DeepSeek R1 via OpenRouter** for AI question generation, resume skill extraction, and final answer review.

## Highlights

- Candidate-friendly Streamlit interface
- Role, experience, and tech-stack based question generation
- Optional PDF/DOCX resume upload for skill extraction
- Step-by-step interview flow with answer box and `Next` navigation
- Final `Save Interview` action that generates the review
- Structured AI feedback with score and recommendation
- Local JSON storage for interview records
- Streamlit Cloud ready

## Demo Flow

1. Enter candidate details.
2. Add tech stack or upload a resume.
3. Click `Start Interview`.
4. Answer each question and click `Next`.
5. Click `Save Interview` after the final question.
6. View the generated interview review.

## Tech Stack

- Python
- Streamlit
- OpenRouter API
- DeepSeek R1
- OpenAI-compatible Python SDK
- pdfplumber
- python-docx
- TextBlob

## Project Structure

```txt
RecruitX/
├── app.py                  # Main Streamlit app and interview flow
├── utils.py                # AI calls, resume parsing, question/review helpers
├── prompts.py              # Reusable prompt text for optional CLI usage
├── chatbot.py              # Optional command-line interview flow
├── requirements.txt        # Python dependencies
├── .env.example            # Local environment variable example
├── .streamlit/config.toml  # Streamlit theme/config
└── README.md
```

## Local Setup

### 1. Clone The Repository

```sh
git clone https://github.com/your-username/RecruitX.git
cd RecruitX
```

### 2. Create A Virtual Environment

Windows:

```sh
python -m venv recruitx_env
recruitx_env\Scripts\activate
```

macOS/Linux:

```sh
python -m venv recruitx_env
source recruitx_env/bin/activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Add Environment Variables

Create a `.env` file in the project root. You can copy `.env.example`.

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=deepseek/deepseek-r1
```

### 5. Run The App

```sh
streamlit run app.py
```

## Streamlit Cloud Deployment

### 1. Push To GitHub

Make sure these files are pushed:

- `app.py`
- `utils.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `.env.example`
- `README.md`

Do not push your real `.env` file. It is already ignored by `.gitignore`.

### 2. Create The Streamlit App

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click `New app`.
3. Select your GitHub repository.
4. Set the main file path to:

```txt
app.py
```

5. Deploy the app.

### 3. Add Streamlit Secrets

In your Streamlit app dashboard:

1. Open `Settings`.
2. Go to `Secrets`.
3. Add:

```toml
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
OPENROUTER_MODEL = "deepseek/deepseek-r1"
```

4. Save and reboot the app.

## Configuration

RecruitX reads configuration from either local environment variables or Streamlit Cloud secrets.

| Variable | Required | Description |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Yes | API key from OpenRouter |
| `OPENROUTER_MODEL` | No | Defaults to `deepseek/deepseek-r1` |
| `APP_URL` | No | Optional OpenRouter referer URL |

## Data And Logs

- Candidate interviews are saved locally to `candidate_details.json`.
- Debug logs are written to `recruitx.log`.
- Both files are ignored by Git.

For production use, replace local JSON storage with a database such as PostgreSQL, Supabase, Firebase, or MongoDB.

## AI Model

Default model:

```txt
deepseek/deepseek-r1
```

You can switch to any OpenRouter chat model by changing `OPENROUTER_MODEL`.

## Notes

- Keep API keys private.
- Do not commit `.env`.
- Streamlit Cloud secrets should be used for the live app.
- Review generated feedback before using it for real hiring decisions.

## License

This project is open for learning, customization, and portfolio use.

