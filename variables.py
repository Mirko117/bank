from dotenv import load_dotenv
import os

load_dotenv()

# Flask
SECRET_KEY = os.getenv("SECRET_KEY")
FLASK_ENV = os.getenv("FLASK_ENV")
FLASK_APP = os.getenv("FLASK_APP")
POS_TERMINAL_ENABLED = os.getenv("POS_TERMINAL_ENABLED", "True").lower() in ("true", "1", "t")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Redis
REDIS_HOSTS = os.getenv("REDIS_HOSTS")

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# API keys
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

# Check if all required environment variables are set
if not all([SECRET_KEY, FLASK_ENV, FLASK_APP, 
            POS_TERMINAL_ENABLED is not None,
            DATABASE_URL, REDIS_HOSTS, CELERY_BROKER_URL,
            CELERY_RESULT_BACKEND, EXCHANGE_RATE_API_KEY]):
    print("\033[91m[WARNING] One or more environment variables are not set. Please check your .env file. Code might not work as intended. If you see this while running tests, you can ignore it.\033[0m")