from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    password_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(50), default='user')  # 'user' or 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_rfid_code = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Card {self.card_rfid_code}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For admin actions
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50))  # 'deposit', 'withdrawal', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.id}>'
