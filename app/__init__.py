from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    #login_manager.init_app(app)

    # Import routes and blueprints
    from app.routes import main
    from app.api.routes import api_bp

    app.register_blueprint(main)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
