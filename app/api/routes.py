from flask import Blueprint, jsonify
from app.models import User

api = Blueprint('api', __name__)

@api.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Fetch user from the database and return JSON data
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'surname': user.surname,
            'balance': user.balance,
            'role': user.role
        })
    # Return a 404 response if the user is not found
    return jsonify({'error': 'User not found'}), 404
