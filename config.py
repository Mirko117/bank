import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXCHANGE_RATE_API_KEY=os.getenv('EXCHANGE_RATE_API_KEY')

# For pytest
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

# For development
class DevelopmentConfig(Config):
    DEBUG = True

# For production
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
