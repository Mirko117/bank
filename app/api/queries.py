from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import db, Transaction, User, ExchangeRate, ExchangeRateLastUpdate
from decimal import Decimal


def calculate_monthly_income_and_change():
    '''Calculate monthly income and change for the current user'''
    # Set timestamp for 30 days ago
    last_month_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())

    # Calculate monthly earnings and expenses
    monthly_earnings = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.receiver_id == current_user.id,
        Transaction.timestamp >= last_month_timestamp,
    ).scalar() or Decimal(0.00)
    monthly_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.timestamp >= last_month_timestamp,
    ).scalar() or Decimal(0.00)

    # Calculate monthly income
    monthly_income = round(monthly_earnings - monthly_expenses, 2)

    return monthly_income

def get_new_currencies():
    '''Get currencies that the user does not have'''
    # Get all currencies
    all_currencies = db.session.query(ExchangeRate.symbol).all()
    all_currencies = [currency[0] for currency in all_currencies]

    # Get user's currencies
    user_currencies = [balance.symbol for balance in current_user.balances]

    # Get new currencies
    new_currencies = list(set(all_currencies) - set(user_currencies))

    return sorted(new_currencies)
