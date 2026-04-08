import os
from flask import Flask
from .extensions import db
from .models import Project, MainDevice, SubDevice, Employee, Problem, DeviceTimeline
from .routes import main_bp, devices_bp, database_bp
from .services import init_db

def create_app(config_name='development'):
    app = Flask(__name__)

    # Configuration
    if config_name == 'development':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fault_registration.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-secret-key'

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(database_bp, url_prefix='/db')

    # Create database tables
    with app.app_context():
        init_db()

    return app