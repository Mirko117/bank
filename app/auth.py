from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User, db, Log
from app.functions import get_translations
import validators
import random
import string


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        t = get_translations()

        if not username:
            return jsonify({"status": t["auth"]["username-required"], "title": t["auth"]["title-error"]}), 400
        
        if not password:
            return jsonify({"status": t["auth"]["password-required"], "title": t["auth"]["title-error"]}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({"status": t["auth"]["invalid-credentials"], "title": t["auth"]["title-error"]}), 401
        
        if not user.check_password(password):
            return jsonify({"status": t["auth"]["invalid-credentials"], "title": t["auth"]["title-error"]}), 401
        
        if user:
            login_user(user)
            return jsonify({"status": t["auth"]["login-successful"], "title": t["auth"]["title-success"]}), 200
        
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('auth/login.html', t=get_translations())

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        t = get_translations()

        if not name:
            return jsonify({"status": t["auth"]["name-required"], "title": t["auth"]["title-error"]}), 400
        if len(name) < 3:
            return jsonify({"status": t["auth"]["name-short"], "title": t["auth"]["title-error"]}), 400
        if any(char.isdigit() for char in name):
            return jsonify({"status": t["auth"]["name-number"], "title": t["auth"]["title-error"]}), 400
        
        if not surname:
            return jsonify({"status": t["auth"]["surname-required"], "title": t["auth"]["title-error"]}), 400
        if len(surname) < 3:
            return jsonify({"status": t["auth"]["surname-short"], "title": t["auth"]["title-error"]}), 400
        if any(char.isdigit() for char in surname):
            return jsonify({"status": t["auth"]["surname-number"], "title": t["auth"]["title-error"]}), 400
        
        if not email:
            return jsonify({"status": t["auth"]["email-required"], "title": t["auth"]["title-error"]}), 400
        if not validators.email(email):
            return jsonify({"status": t["auth"]["email-invalid"], "title": t["auth"]["title-error"]}), 400
        
        if not password:
            return jsonify({"status": t["auth"]["password-required"], "title": t["auth"]["title-error"]}), 400
        if len(password) <= 6:
            return jsonify({"status": t["auth"]["password-short"], "title": t["auth"]["title-error"]}), 400
        if not any(char.isdigit() for char in password):
            return jsonify({"status": t["auth"]["password-number"], "title": t["auth"]["title-error"]}), 400

        if password != confirm_password:
            return jsonify({"status": t["auth"]["password-mismatch"], "title": t["auth"]["title-error"]}), 400

        if User.query.filter_by(email=email).first() is not None:
            return jsonify({"status": t["auth"]["email-exists"], "title": t["auth"]["title-error"]}), 400
        
        # Generate username
        username = surname.lower()[:2] + name.lower()[:2]
        username += "".join(random.choices(string.digits, k=4))

        # Check if username already exists, if so, add another 4 random digits
        while User.query.filter_by(username=username).first() is not None:
            username[:4] += "".join(random.choices(string.digits, k=4))

        # Create new user
        new_user = User(username=username, first_name=name, last_name=surname, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # TODO: Send email to user with his username

        return jsonify({"status": t["auth"]["registration-successful"], "title": t["auth"]["title-success"]}), 201

    return render_template('auth/register.html', t=get_translations())

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))