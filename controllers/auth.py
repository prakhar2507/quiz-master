from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from models.user import User
from models.admin import Admin
from extensions import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# ✅ User Registration
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        qualification = request.form['qualification']
        dob_str = request.form['dob']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for('auth.user_login'))

        # ✅ Convert 'dob' string to 'datetime.date' object
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

        # ✅ Create and save new user
        new_user = User(email=email, full_name=full_name, qualification=qualification, dob=dob)
        new_user.set_password(password)  # Hash the password before saving
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.user_login'))

    return render_template('register.html')  # ✅ Use 'register.html' for user registration


# ✅ User Login
@auth_bp.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session.clear()
            login_user(user, remember=True, force=True)
            session['user_type'] = 'user'
            session['user_id'] = str(user.id)
            session['logged_in'] = True
            
            flash("User login successful!", "success") # Get the next parameter or default to dashboard
            next_page = request.args.get('next')
            # Redirect to next page or dashboard
            return redirect(next_page or url_for('user.dashboard'))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template('users/user_login.html')

# ✅ Admin Login
@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            session.clear()
            login_user(admin, remember=True, force=True)
            session['user_type'] = 'admin'
            session['user_id'] = str(admin.id)
            session['logged_in'] = True 
            
            flash("Admin login successful!", "success")
            return redirect(url_for('admin.dashboard'))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template('admin/admin_login.html')

# ✅ Logout (Common for Admin & User)
@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('routes.landing'))  # Redirect to user login by default