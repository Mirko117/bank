import variables


class Config:
    SECRET_KEY = variables.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = variables.DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXCHANGE_RATE_API_KEY = variables.EXCHANGE_RATE_API_KEY

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

# For Celery
class CeleryConfig:
    broker_url = variables.CELERY_BROKER_URL
    result_backend = variables.CELERY_RESULT_BACKEND
    task_ignore_result = True

