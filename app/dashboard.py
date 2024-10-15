from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/')
@login_required
def index():
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return redirect(url_for('dashboard.user'))
        elif current_user.role == 'admin':
            return redirect(url_for('dashboard.admin'))

@dashboard.route('/user')
@login_required
def user():
    if current_user.is_authenticated:
        return render_template('dashboard/user.html')


@dashboard.route('/admin')
@login_required
def admin():
    if current_user.is_authenticated:
        return render_template('dashboard/admin.html')