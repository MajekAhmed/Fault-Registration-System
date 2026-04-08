import os
from flask import Flask
from .extensions import db
from .models import Project, MainDevice, SubDevice, Employee, Problem, DeviceTimeline
from .routes import main_bp, devices_bp, database_bp
from .services import init_db, create_default_data

def create_app(config_name='development'):
    app = Flask(__name__)

    # Configuration - Ready for PostgreSQL migration
    if config_name == 'development':
        # For easy development, using SQLite
        # To migrate to PostgreSQL, change to:
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fault_registration.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-secret-key'
    elif config_name == 'production':
        # Production config with PostgreSQL
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'prod-secret-key')

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(database_bp, url_prefix='/db')

    # Create database tables
    with app.app_context():
        init_db()
        # Create default tenant and user if not exists
        create_default_data()

    return app