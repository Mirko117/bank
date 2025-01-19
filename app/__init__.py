from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_object='config.Config'):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_object)
    login_manager.login_view = 'auth.login'

    # Set Jinja environment
    from app.jinja import set_jinja_environment
    set_jinja_environment(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.api.routes import api_bp
    from app.dashboard import dashboard_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    return app
