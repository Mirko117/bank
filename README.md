# Web Bank
## How to run

1. Install needed pip libraries by running (using virtualenv is suggested):

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables:

- In the project directory, create a `.env` file with the following content:

    ```makefile
    SECRET_KEY="your_secret_key"
    FLASK_ENV="production" # or deveopment
    DATABASE_URL="postgresql://username:password@localhost/
    web_bank_db"
    EXCHANGE_RATE_API_KEY="api_key"

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

## Testing

### Tests
You can run tests by typing `pytest` in terminal.

### Mock data for testing UI
Run:
```bash
python scripts/generate_mock_data.py
```