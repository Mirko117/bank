from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.functions import get_user_translations


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return redirect(url_for('dashboard.user'))
        elif current_user.role == 'admin':
            return redirect(url_for('dashboard.admin'))

@dashboard_bp.route('/user')
@login_required
def user():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('dashboard.admin'))
        return render_template('dashboard/user.html', t=get_user_translations(), user=current_user)

@dashboard_bp.route('/admin')
@login_required
def admin():
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return redirect(url_for('dashboard.user'))
        return render_template('dashboard/admin.html', t=get_user_translations(), user=current_user)