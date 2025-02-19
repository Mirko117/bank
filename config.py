import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXCHANGE_RATE_API_KEY=os.getenv('EXCHANGE_RATE_API_KEY')

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True