from flask import Blueprint, jsonify
from flask_restx import Api, Resource, Namespace
from app.models import User


# Create blueprint, API and namespace
api_bp = Blueprint('api', __name__)
api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")


@api_ns.route('/users')
class UsersEndpoint(Resource):
    def get(self):
        users = User.query.all()
        return jsonify([user.serialize() for user in users])


# Add namespace to API
api.add_namespace(api_ns, path='/')