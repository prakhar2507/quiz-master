from datetime import datetime
from flask import Flask
from models.quiz import Quiz
from extensions import db, migrate, login_manager


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SECRET_KEY'] = 'quiz-master'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.landing'

    from controllers.user import user_bp  # Import inside the function to avoid circular imports
    app.register_blueprint(user_bp)
    from controllers.auth import auth_bp
    app.register_blueprint(auth_bp)
    from controllers.admin import admin_bp
    app.register_blueprint(admin_bp)
    from controllers.routes import routes_bp
    app.register_blueprint(routes_bp)

    return app