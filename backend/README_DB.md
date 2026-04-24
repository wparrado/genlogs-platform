Database and migrations

This folder contains Alembic configuration and SQLModel models used by the GenLogs backend.

Usage:

- To create the database schema locally for development (uses SQLModel metadata):

    python -c "from app.db import init_db; init_db()"

- To run Alembic migrations (recommended for production):

    alembic -c alembic.ini upgrade head

- To seed minimal required data for the MVP:

    python backend/scripts/seed_data.py

Notes:
- The SQLModel models live in app/models/db_models.py and are the canonical source for table definitions.
- Alembic env is configured to use the application settings (app.config.settings) for the DB URL.
