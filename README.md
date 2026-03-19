# MiBank – Web Banking Application

A full-stack banking simulation web app built with **Flask, PostgreSQL, Redis, Celery, Docker, Gunicorn, and Nginx.**

## Project Overview

MiBank allows users to:
- Register/login and manage accounts
- View transaction history
- Perform transfers
- Track currency data
- Provides an admin dashboard for user management

This project demonstrates:
- Monolithic web architecture with async task processing (Celery + Redis)
- Containerized local/prod workflows with Docker Compose
- Relational data modeling and migrations (PostgreSQL + Flask-Migrate)
- Reverse proxy deployment setup (Nginx + Gunicorn)

### Demo
- Screenshots, sitemap, architecture, and DB schema: [docs/demo.md](./docs/demo.md)

## How to run

### Local development

1. Install needed pip libraries by running (using virtualenv is suggested):

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables:

This project uses two .env files. They should be called `.env.local` and `.env.docker`. In the projects root you have examples of how they should look and what they should contain. Main difference between then is that when running docker, you need to point to other services that are running by using that services names as host (e.g. `postgres` for PostgreSQL, `redis` for Redis), but for the local development (when running `python manage.py`) variables need to point to `localhost` instead. 

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
- **Note for Docker:** You can basically run applications in 2 modes, development and production. Production is imagined to be running on some sort of Linux Server and inside Docker containers. For that you will need Nginx reverse proxy. If you want to run it in development mode locally, you don't need Nginx container running, you only Postgres (if working with Postgres, if not then you can simply use SQLite), Redis, Redis Commander and Celery. When you have all 4 containers set up then you can run command above.

5. Access the website

- Open a browser and navigate to `http://localhost:5000` to view the web bank.

### Docker environment
1. Install Docker and Docker Compose on your machine.

2. Create same `.env` files as told above.

3. For setting up docker, you can use commands from Makefile, run `make up` to start all containers and then you can run `make local` to stop Nginx and Flask container so you can run Flask directly.

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
Change `mibank.si` to your domain, also change it in `nginx.ssl.conf`

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
