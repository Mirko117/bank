from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import time

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    role = db.Column(db.String(50), default='user', nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False) # Unix timestamp

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'success', 'failed', etc.
    transaction_type = db.Column(db.String(50), nullable=False)  # 'deposit', 'withdrawal', etc.
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def __repr__(self):
        return f'<Transaction {self.id}>'


class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rfid_code = db.Column(db.String(100), unique=True, nullable=False)
    pin_hash = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='active', nullable=False)  # 'active', 'blocked', etc.
    created_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def __repr__(self):
        return f'<Card {self.rfid_code}>'


class Settings(db.Model):
    __tablename__ = 'settings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    language = db.Column(db.String(2), nullable=False, default='en')  # 'en', 'si'
    user = db.relationship('User', backref=db.backref('settings', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Settings {self.user_id}, {self.language}>'


