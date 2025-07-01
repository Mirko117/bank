import variables
from app import create_app

FLASK_ENV = variables.FLASK_ENV

if FLASK_ENV == 'development':
    app = create_app(config_object='config.DevelopmentConfig')
elif FLASK_ENV == 'production':
    app = create_app(config_object='config.ProductionConfig')
else:
    raise ValueError('FLASK_ENV not set properly')

# Tetsing environment is run seperately

# Initialize Celery
from app.extensions import celery_init_app
celery = celery_init_app(app)

if __name__ == '__main__':
    app.run()
