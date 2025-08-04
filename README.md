# MiBank - Web Bank Application

This application is my middle school final project. It's a web bank application that allows users to manage their accounts, view transactions, and perform various banking operations. The application uses tools like **Flask and Flask extensions, jQuery, PostgreSQL, Docker, Redis, Celery, Gunicorn, and Nginx**.

## How to run

### Local development

1. Install needed pip libraries by running (using virtualenv is suggested):

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables:

- In the project directory, create a `.env` file with the following content:

    ```makefile
    # Flask
    SECRET_KEY="your_secret_key"
    FLASK_ENV="production" # or development
    FLASK_APP="manage.py"
    POS_TERMINAL_ENABLED="False" # or True

    # Database
    DATABASE_URL="postgresql://username:password@localhost/web_bank_db"

    # Redis
    REDIS_HOSTS="localhost:6379"

    # Celery
    CELERY_BROKER_URL="redis://localhost:6379/0"
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"

    # Cache
    CACHE_REDIS_URL="redis://localhost:6379/0"

    # API keys
    EXCHANGE_RATE_API_KEY="api_key"

    # Docker
    POSTGRES_DB="postgres_db"
    POSTGRES_USER="postgres_user"
    POSTGRES_PASSWORD="postgres_password"

    ```
- If you get some sort of connectivity error, try changing `redis://localhost:6379/0` to `redis://redis_cache:6379/0`

- If you want to use SQLite:

    ```makefile
    DATABASE_URL="sqlite:///web_bank_db.sqlite3"
    ```

3. Set up the database

- If using Docker you can skip this step since the database will be initialized inside container.

- Ensure PostgreSQL is installed and running on your machine.

- Apply the database migrations by running:
    ```bash
    flask db upgrade
    ```

4. Start the Flask application

- Run the following command to start the web server:

    ```bash
    python manage.py
    ```
- **Note for Docker:** You can basically run applications in 2 modes, development and production. Production is imagined to be running on some sort of Linux Server and inside Docker containers. For that you will need Nginx reverse proxy. If you want to run it in development mode locally, you don't need Nginx container running, you only need Postgres (if working with Postgres, if not then you can simply use SQLite), Redis and Redis Commander. When you have all 3 containers set up then you can run command above.

5. Access the website

- Open a browser and navigate to `http://localhost:5000` to view the web bank.

### Docker environment
1. Install Docker and Docker Compose on your machine.

2. Create same `.env` file as in local development (see above).

3. Build and run the Docker containers:

    ```bash
    sudo docker-compose up --build -d
    ```

## SSL

This is optional, but if you want to use SSL, you can use Certbot with Let's Encrypt.

```bash
sudo apt install certbot

docker-compose down

sudo certbot certonly --standalone -d mibank.si -d www.mibank.si

mkdir ./ssl # in project root folder

sudo cp /etc/letsencrypt/live/mibank.si/fullchain.pem ./ssl/

sudo cp /etc/letsencrypt/live/mibank.si/privkey.pem ./ssl/

sudo chown -R $USER:$USER ./ssl/
```
Change `mibank.si` to your domain, also change it in `nginx.conf`

## Testing
You can run tests by typing `pytest` in terminal.

## Scripts

### Note for Docker: Use next command to run scripts:
```bash
sudo docker exec -it flask_app sh -c "SCRIPT"
```

### Mock data for testing UI
It will generate random users with random data. I used it for testing UI.
```bash
python scripts/generate_mock_data.py
```

### Set admin
It will set user as admin.
```bash
python scripts/set_admin.py username
```

### Watch Celery tasks
```bash
celery -A manage.celery worker --loglevel INFO
```
