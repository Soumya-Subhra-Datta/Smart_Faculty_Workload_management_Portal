"""
=============================================================================
Faculty Workload Scheduling & Substitution Portal
Sathyabama Institute of Science and Technology
=============================================================================
Main Flask application entry point.
"""
import atexit
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.faculty import faculty_bp
from services.scheduler import init_scheduler, shutdown_scheduler
from datetime import timedelta
import os

# ── Create Flask App ──
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# ── Configuration ──
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# ── Extensions ──
CORS(app)
jwt = JWTManager(app)

# ── Register Blueprints ──
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(faculty_bp)

# ── Serve SPA ──
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files or fall back to SPA index."""
    if path.startswith('static/'):
        return send_from_directory('.', path)
    if path.startswith('api/'):
        return {'error': 'Not found'}, 404
    return send_from_directory('templates', 'index.html')


# ── JWT Error Handlers ──
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'error': 'Token has expired', 'code': 'token_expired'}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'error': 'Invalid token', 'code': 'invalid_token'}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {'error': 'Authorization required', 'code': 'authorization_required'}, 401


# ── Start ──
if __name__ == '__main__':
    # Initialize background scheduler
    init_scheduler(app)
    atexit.register(shutdown_scheduler)

    print()
    print("=" * 60)
    print("  Faculty Workload Portal — Running")
    print(f"  URL: http://localhost:{Config.FLASK_PORT}")
    print("=" * 60)
    print()

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.DEBUG,
        use_reloader=False  # Disable reloader to prevent double scheduler
    )
