from flask import request, make_response
from flask_restx import Resource, Namespace
from app.api import api


# Create namespace for POS routes
pos_ns = Namespace("pos", description="POS operations")


@pos_ns.route('/lorem')
class PosLoremEndpoint(Resource):
    def get(self):
        response = make_response({"status": "success", "message": "Lorem ipsum dolor sit amet"}, 200)
        return response
