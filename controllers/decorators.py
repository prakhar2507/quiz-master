from functools import wraps
from flask import flash, redirect, url_for, session
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and has admin role
        if not current_user.is_authenticated or session.get('user_type') != 'admin':
            flash("Unauthorized access! Admin privileges required.", "danger")
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and has user role
        if not current_user.is_authenticated or session.get('user_type') != 'user':
            flash("Unauthorized access! Please login as user.", "danger")
            return redirect(url_for('auth.user_login'))
        return f(*args, **kwargs)
    return decorated_function
