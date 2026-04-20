"""
Authentication routes — Login, token management.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from models import user as user_model
from datetime import timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    user = user_model.authenticate(data['username'], data['password'])
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    # Create JWT token with user identity
    additional = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'full_name': user['full_name'],
        'department': user['department']
    }
    access_token = create_access_token(
        identity=str(user['id']),
        additional_claims=additional,
        expires_delta=timedelta(hours=24)
    )

    return jsonify({
        'token': access_token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email'],
            'department': user['department'],
            'role': user['role'],
            'subjects': user.get('subjects', [])
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get the current authenticated user's profile."""
    user_id = int(get_jwt_identity())
    user = user_model.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user}), 200
