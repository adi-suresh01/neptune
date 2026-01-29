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
