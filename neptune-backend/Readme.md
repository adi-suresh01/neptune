## Backend Installation and Startup

### PostgreSQL Installation and Setup

1. Install PostgreSQL using Homebrew:
    ```bash
    brew install postgresql@14
    brew services start postgresql@14
    ```

2. Create database and user:
    ```bash
    psql postgres
    # Inside PostgreSQL shell
    CREATE USER adi WITH PASSWORD 'yourpassword';
    CREATE DATABASE neptune;
    GRANT ALL PRIVILEGES ON DATABASE neptune TO adi;
    \q
    ```

3. Create .env file:
    ```bash
    # Create the file
    touch .env

    # Add database connection string
    echo "DATABASE_URL=postgresql://adi:yourpassword@localhost:5432/neptune" > .env
    ```

4. Install Python dependencies:
    ```bash
    pip install fastapi uvicorn sqlalchemy psycopg2-binary asyncpg pydantic alembic python-dotenv
    ```

5. Initialize Alembic:
    ```bash
    alembic init alembic
    ```

6. Generate migration files:
    ```bash
    alembic revision --autogenerate -m "Initial migration"
    ```

7. Apply migration:
    ```bash
    alembic upgrade head
    ```

8. Starting the server:
    ```bash
    uvicorn app.main:app --reload
    ```

9. Access API documentation:
    ```
    http://localhost:8000/docs
    ```

## Desktop Mode (SQLite)

- Use SQLite for zero-config local storage:
  ```bash
  export NEPTUNE_MODE=desktop
  export DB_BACKEND=sqlite
  export NEPTUNE_DESKTOP_DIR=~/.neptune
  ```
- The database will be created at `~/.neptune/neptune.db`.

## Search

- SQLite mode uses FTS5 by default.
- Configuration:
  - `SEARCH_MODE=auto|fts|fallback`
  - `SEARCH_MIN_QUERY_LEN` (default: 2)
  - `SEARCH_MAX_RESULTS` (default: 50)
- Endpoint:
  - `GET /api/search?q=your+query`

## Revisions

- Note revisions are saved automatically on update.
- Configuration:
  - `MAX_NOTE_REVISIONS` (default: 20)
- Endpoint:
  - `GET /api/revisions/{file_id}`

## Storage and Filesystem Design

- The filesystem API is metadata-first for scale.
- List endpoint returns metadata only; content is fetched separately.
- Content storage is configurable:
  - `STORAGE_MODE=db` stores content in the database.
  - `STORAGE_MODE=dual` stores content in both DB and object storage.
  - `STORAGE_MODE=s3` stores content only in object storage.

Key endpoints:
- `GET /api/filesystem` returns metadata with pagination.
- `GET /api/filesystem/{id}` returns full item and content.
- `GET /api/filesystem/{id}/content` returns content only.
- `PUT /api/filesystem/{id}/content` updates content.

Related environment variables:
- `STORAGE_MODE`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`
- `MAX_NOTE_BYTES` to limit note size.

## Knowledge Graph Design

- Topic extraction uses the LLM once per note.
- Relationship scoring uses the LLM in batches with deterministic fallback.
- Graph size and strength thresholds are configurable:
  - `KG_MIN_STRENGTH`
  - `KG_MAX_EDGES`
  - `KG_CACHE_VERSION`

## Shared Ollama Service

- The backend expects a shared Ollama service when `OLLAMA_SHARED=true`.
- Configure:
  - `OLLAMA_URL=http://<tailscale-ip>:11434`
  - `OLLAMA_TEMPERATURE`, `OLLAMA_TOP_P`, `OLLAMA_MAX_TOKENS`
  - `LLM_TOPIC_BATCH_SIZE`, `LLM_REL_BATCH_SIZE`

## Ubuntu Server Deployment (Tailscale + systemd)

1. Install system dependencies:
    ```bash
    sudo apt update
    sudo apt install -y python3-venv python3-dev build-essential
    ```

2. Create a virtual environment:
    ```bash
    cd /opt/neptune/neptune-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Configure environment variables:
    ```bash
    cp .env.example .env
    ```
    Recommended values:
    - `NEPTUNE_ENV=production`
    - `NEPTUNE_MODE=server`
    - `HOST=0.0.0.0`
    - `PORT=8000`
    - `CORS_ORIGINS=https://your-domain.com`
    - `OLLAMA_URL=http://<tailscale-ip>:11434`
    - `STORAGE_MODE=dual` (optional)
    - `S3_ENDPOINT=http://<tailscale-ip>:9000` (optional)

4. Create a systemd service:
    ```ini
    [Unit]
    Description=Neptune Backend
    After=network.target

    [Service]
    WorkingDirectory=/opt/neptune/neptune-backend
    ExecStart=/opt/neptune/neptune-backend/venv/bin/python -m app.server
    EnvironmentFile=/opt/neptune/neptune-backend/.env
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

5. Enable and start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable neptune-backend
    sudo systemctl start neptune-backend
    sudo systemctl status neptune-backend
    ```

6. Health check:
    ```bash
    curl http://localhost:8000/health
    curl http://localhost:8000/api/system/ready
    ```
