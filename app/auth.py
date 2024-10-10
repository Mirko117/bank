from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from flask_login import login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, db
from app.functions import get_translations
import validators


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if not username:
            return jsonify({"status": "Username is required"}), 400
        
        if not password:
            return jsonify({"status": "Password is required"}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({"status": "Invalid credentials"}), 401
        
        if not check_password_hash(user.password_hash, password):
            return jsonify({"status": "Invalid credentials"}), 401
        
        if user:
            login_user(user)
            return jsonify({"status": "Logged in successfully"}), 200

    return render_template('login.html', t=get_translations())

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if not name:
            return jsonify({"status": "Name is required"}), 400
        if len(name) < 3:
            return jsonify({"status": "Name is too short"}), 400
        if any(char.isdigit() for char in name):
            return jsonify({"status": "Name must not contain a number"}), 400
        
        if not surname:
            return jsonify({"status": "Surname is required"}), 400
        if len(surname) < 3:
            return jsonify({"status": "Surname is too short"}), 400
        if any(char.isdigit() for char in surname):
            return jsonify({"status": "Surname must not contain a number"}), 400
        
        if not email:
            return jsonify({"status": "Email is required"}), 400
        if not validators.email(email):
            return jsonify({"status": "Invalid email"}), 400
        
        if not password:
            return jsonify({"status": "Password is required"}), 400
        if len(password) <= 6:
            return jsonify({"status": "Password is too short"}), 400
        if not any(char.isdigit() for char in password):
            return jsonify({"status": "Password must contain a number"}), 400

        if password != confirm_password:
            return jsonify({"status": "Passwords do not match"}), 400

        if User.query.filter_by(email=email).first() is not None:
            return jsonify({"status": "Email already exists"}), 400
        
        username = email.split('@')[0]

        if User.query.filter_by(username=username).first() is not None:
            username = username + str(User.query.filter_by(username=username).count() + 1)

        new_user = User(username=username, name=name, surname=surname, email=email, password_hash=generate_password_hash(password))

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"status": "User created successfully"}), 201

    return render_template('register.html', t=get_translations())

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))