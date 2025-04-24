import variables
from flask import Blueprint
from flask_restx import Api, Namespace
from app.api.admin_dashboard_routes import admin_dashboard_ns
from app.api.dashboard_routes import dashboard_ns
from app.api.pos_routes import pos_ns


# Create blueprint, API and namespace for API
api_bp = Blueprint('api', __name__)
if variables.FLASK_ENV == "production":
    api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API", doc=False)
else:
    api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")

# Add namespaces to API
api.add_namespace(api_ns, path='/')
api.add_namespace(dashboard_ns, path='/dashboard')
api.add_namespace(admin_dashboard_ns, path='/admin-dashboard')

if variables.POS_TERMINAL_ENABLED:
    # Add POS namespace to API if enabled
    api.add_namespace(pos_ns, path='/pos')

