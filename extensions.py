from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask import session


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    from models.admin import Admin
    user_type = session.get('user_type')  # Check user type stored in session
    
    if user_type == "user":
        return User.query.get(int(user_id))
    elif user_type == "admin":
        return Admin.query.get(int(user_id))
    
    return None  # Return None if user_type is missing
