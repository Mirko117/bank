from app import db
from flask import session, has_request_context
from sqlalchemy import event
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
import time

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user', nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False) # Unix timestamp

    def set_password(self, password):
        # Need to commit the session after calling this method
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_balance(self, symbol):
        balance = self.balances.filter_by(symbol=symbol).first()
        return balance.amount if balance else Decimal(0.00)
    
    def add_balance(self, amount, symbol):
        # Need to commit the session after calling this method
        balance = self.balances.filter_by(symbol=symbol).first()
        if balance:
            balance.amount += Decimal(amount)
        else:
            balance = Balance(user_id=self.id, symbol=symbol, amount=amount)
            db.session.add(balance)

    def remove_balance(self, amount, symbol):
        # Need to commit the session after calling this method
        balance = self.balances.filter_by(symbol=symbol).first()
        if balance:
            balance.amount -= Decimal(amount)
    
    # Relationship to transactions
    transactions = db.relationship(
        'Transaction',
        primaryjoin="or_(User.id == Transaction.user_id, User.id == Transaction.receiver_id)",
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<User {self.username}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), default=".", nullable=False) # 'Spotify', 'Netflix', etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='EUR')  # 'EUR', 'USD', etc.
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'success', 'failed', etc.
    transaction_type = db.Column(db.String(50), nullable=False)  # 'deposit', 'withdrawal', etc.
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def __repr__(self):
        return f'<Transaction {self.id}, {self.amount}, {self.status}>'


class Balance(db.Model):
    __tablename__ = 'balances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(3), nullable=False, default='EUR')  # 'EUR', 'USD', etc.
    amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)
    user = db.relationship('User', backref=db.backref('balances', lazy='dynamic'))

    def __repr__(self):
        return f'<Balance {self.id}, {self.symbol}, {self.amount}>'


class BalanceHistory(db.Model):
    __tablename__ = 'balance_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(3), nullable=False, default='EUR')  # 'EUR', 'USD', etc.
    amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)


    def __repr__(self):
        return f'<BalanceHistory {self.id}, {self.symbol}, {self.amount}>'

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(3), unique=True, nullable=False)
    rate = db.Column(db.Numeric(15, 4), nullable=False)

    def __repr__(self):
        return f'<ExchangeRate {self.symbol}, {self.rate}>'
    

class ExchangeRateLastUpdate(db.Model):
    __tablename__ = 'exchange_rates_last_update'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def __repr__(self):
        return f'<ExchangeRateLastUpdate {self.timestamp}>'


class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rfid_code = db.Column(db.String(100), unique=True, nullable=False)
    pin_hash = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='active', nullable=False)  # 'active', 'blocked', etc.
    created_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def set_pin(self, pin):
        # Need to commit the session after calling this method
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def __repr__(self):
        return f'<Card {self.rfid_code}, {self.status}>'


class Settings(db.Model):
    __tablename__ = 'settings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    language = db.Column(db.String(2), nullable=False, default='en')  # 'en', 'si'
    default_currency = db.Column(db.String(3), nullable=False, default='EUR')  # 'EUR', 'USD', etc.
    user = db.relationship('User', backref=db.backref('settings', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Settings {self.user_id}, {self.language}>'

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    action_type = db.Column(db.String(100), nullable=False) # 'login', 'logout', 'transaction', etc.
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='success', nullable=False)  # 'success', 'failed', etc.
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)

    def __repr__(self):
        return f'<Log {self.id}, {self.action_type}, {self.status}>'


# Automatically add settings when a user is created
@event.listens_for(User, 'after_insert')
def create_settings(mapper, connection, target):
    # Check if there's a request context and use 'lang' from the session if available
    # This is used for testing purposes (when populating with mock users/data)
    if has_request_context():
        language = session.get('lang', 'en')
    else:
        language = 'en'
    
    # Insert the default settings for the user
    # Replacement of the following code:
    # db.session.add(Settings(user_id=target.id, language=language, default_currency='EUR'))
    connection.execute(
        Settings.__table__.insert().values(
            user_id=target.id,
            language=language,
            default_currency='EUR'
        )
    )


# Automatically add a balance when a user is created
@event.listens_for(User, 'after_insert')
def create_balance(mapper, connection, target):
    # Insert the default balance for the user
    # Replacement of the following code:
    # db.session.add(Balance(user_id=target.id, symbol='EUR', amount=0.00))
    connection.execute(
        Balance.__table__.insert().values(
            user_id=target.id,
            symbol='EUR',
            amount=0.00
        )
    )

# Automatically add a balance history when a user is created
@event.listens_for(User, 'after_insert')
def create_balance_history(mapper, connection, target):
    # Insert the default balance history for the user
    connection.execute(
        BalanceHistory.__table__.insert().values(
            user_id=target.id,
            symbol='EUR',
            amount=0.00
        )
    )

# Automatically add balanbe history when a balance is updated
@event.listens_for(Balance, 'after_update')
def create_balance_history(mapper, connection, target):
    # Insert the default balance history for the user
    connection.execute(
        BalanceHistory.__table__.insert().values(
            user_id=target.user_id,
            symbol=target.symbol,
            amount=target.amount
        )
    )
