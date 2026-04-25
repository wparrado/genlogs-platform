GenLogs backend

Local development

1. Create a .env file from the provided example and fill in secrets:

   cp .env.example .env
   # Edit .env and set GENLOGS_GOOGLE_API_KEY and any other values.

2. To export the variables and run the application locally (bash):

   set -a && source .env && set +a && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

Notes
- The settings loader reads from a .env file by default (see src/app/config/settings.py).
- Ensure your Python virtualenv is activated and dependencies are installed before running.
