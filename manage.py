from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

FLASK_ENV = os.getenv('FLASK_ENV')

if FLASK_ENV == 'development':
    app = create_app(config_object='config.DevelopmentConfig')
elif FLASK_ENV == 'production':
    app = create_app(config_object='config.ProductionConfig')
else:
    raise ValueError('FLASK_ENV not set properly')

# Tetsing environment is run seperately

if __name__ == '__main__':
    app.run()
