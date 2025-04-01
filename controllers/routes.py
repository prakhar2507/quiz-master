from flask import render_template, Blueprint

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def landing():
    return render_template('index.html')