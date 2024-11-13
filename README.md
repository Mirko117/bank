# Web Bank

## Description

This project will have two components: physical and virtual.

The virtual component will be the bank's website, where users will be able to log into their accounts, view their balance, transfer money and perform other banking tasks. The website will be hosted on a Linux server.

The physical component will be the POS terminal, built using an ESP32 microcontroller. It will feature an RFID sensor, keypad, and display screen, with the potential addition of a buzzer and/or LED indicator. The microcontroller will have an internet connection to send requests to the server.

## Image of the architecture

<div align="center">
    <img src="images/Architecture.png">
</div>

## How to run

1. Install needed pip libraries by running:

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables:

- In the project directory, create a `.env` file with the following content:

    ```makefile
    SECRET_KEY="your_secret_key"
    DATABASE_URL="postgresql://username:password@localhost/web_bank_db"
    ```

- If you want to use SQLite it also should work by adding

    ```makefile
    DATABASE_URL="sqlite:///web_bank_db.sqlite3"
    ```

3. Set up the database

- Ensure PostgreSQL is installed and running on your machine
- Create a database for the project using the following command:

    ```
    createdb web_bank_db
    ```

- Apply the database migrations by running:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

4. Start the Flask application

- Run the following command to start the web server:

    ```bash
    py manage.py
    ```

- If it doesn't work also try:

    ```bash
    python manage.py
    ```

- or

    ```bash
    python3 manage.py
    ```

5. Access the website

- Open a browser and navigate to `http://localhost:5000` to view the web bank.

## Testing

You can run tests by typing `pytest` in terminal.