from flask import Blueprint, jsonify, request, render_template, make_response
from flask_restx import Api, Resource, Namespace
from flask_login import current_user
from app.functions import get_user_translations


# Create blueprint, API and namespace for API
api_bp = Blueprint('api', __name__)
api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")

# Create namespace for dashboard
dashbpard_ns = Namespace("dashboard", description="Dashboard operations")

@dashbpard_ns.route('/get-shell')
class DashboardGetPageEndpoint(Resource):
    def get(self):
        shell = request.args.get('shell')
        
        if not shell:
            response = make_response({"status": "error", "message": "No shell provided"}, 400)
            return response

        try:
            # Render the shell
            rendered_shell = render_template(f"dashboard/shells/{shell}.html", t=get_user_translations(), user=current_user)
        except Exception as e:
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response   

        if not rendered_shell:
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response

        # Return the rendered shell
        response = make_response({"status": "success", "shell": rendered_shell}, 200)
        return response

# Add namespaces to API
api.add_namespace(api_ns, path='/')
api.add_namespace(dashbpard_ns, path='/dashboard')
