# Web Bank
## How to run

1. Install needed pip libraries by running (using virtualenv is suggested):

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables:

- In the project directory, create a `.env` file with the following content:

    ```makefile
    # Flask
    SECRET_KEY="your_secret_key"
    FLASK_ENV="production" # or deveopment

    # Database
    DATABASE_URL="postgresql://username:password@localhost/
    web_bank_db"

    # API keys
    EXCHANGE_RATE_API_KEY="api_key"

    # Docker
    POSTGRES_DB="postgres_db"
    POSTGRES_USER="postgres_user"
    POSTGRES_PASSWORD="postgres_password"

    ```

- If you want to use SQLite:

    ```makefile
    DATABASE_URL="sqlite:///web_bank_db.sqlite3"
    ```

3. Set up the database

- Ensure PostgreSQL is installed and running on your machine
- Create a database for the project using the following command (if you plan to tun on sqlite3 you should skip this step):

    ```
    createdb web_bank_db
    ```

- Apply the database migrations by running:
    ```bash
    flask db upgrade
    ```

4. Start the Flask application

- Run the following command to start the web server:

    ```bash
    python manage.py
    ```

5. Access the website

- Open a browser and navigate to `http://localhost:5000` to view the web bank.

## Docker
If you'd like to run it using Docker:
```bash
docker-compose up --build -d
```
## SSL
```bash
sudo apt install certbot

docker-compose down

sudo certbot certonly --standalone -d mibank.si -d www.mibank.si

mkdir ./ssl # in project root folder

sudo cp /etc/letsencrypt/live/mibank.si/fullchain.pem ./ssl/

sudo cp /etc/letsencrypt/live/mibank.si/privkey.pem ./ssl/

sudo chown -R $USER:$USER ./ssl/
```
Change `mibank.si` to yout domain, also change it in `nginx.conf`

## Testing
You can run tests by typing `pytest` in terminal.

## Scripts

### Mock data for testing UI
It will generate random users with random data. I used it for testing UI.
```bash
python scripts/generate_mock_data.py
```

### Set admin
It will set user as admin.
```
python scripts/set_admin.py username
```