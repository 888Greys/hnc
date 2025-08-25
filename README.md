HNC - Questionnaire Prototype

This workspace contains a Streamlit-based prototype for digitizing client questionnaires and generating initial legal proposals (mocked AI). Files:

- `questionnaire_prototype.py` - Streamlit app (prototype).
- `client_data.json` - Example or saved client data.
- `clientbrief.md`, `requirements.md`, `research.md` - project docs.
- `requirements.txt` - Python dependencies for the prototype.

Quick start (macOS, zsh):

1. Create a virtual environment and activate it (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run questionnaire_prototype.py
```

Notes:
- The app uses a mock Kenya Law snippet by default. To enable Cerebras calls, install the `cerebras-cloud-sdk` package and set the `CEREBRAS_API_KEY` environment variable.
- This prototype saves client data to `client_data.json` in the workspace root. For production, implement encrypted storage and proper auth.
- The code is intentionally simple to allow fast iteration and demoing. See `requirements.md` for project goals and scope.
