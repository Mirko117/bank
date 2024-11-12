from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    surname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    #balance = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(50), default='user')  # 'user' or 'admin'

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "role": self.role
        }

    def __repr__(self):
        return f'<User {self.username}>'

'''
dont need this right now. still not sure how it all should be structured
commenting out for now, will need later

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rfid_code = db.Column(db.String(50), unique=True, nullable=False)
    pin = db.Column(db.String(4), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Card {self.card_rfid_code}>'

class Terminal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    terminal_id = db.Column(db.String(50), unique=True, nullable=False)
    location = db.Column(db.String(150))
    status = db.Column(db.String(50), default='active')  # active, maintenance, etc.

    def __repr__(self):
        return f'<Terminal {self.terminal_id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For admin actions
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50))  # 'deposit', 'withdrawal', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    terminal_id = db.Column(db.String(50), db.ForeignKey('terminal.terminal_id')) 

    def __repr__(self):
        return f'<Transaction {self.id}>'
'''