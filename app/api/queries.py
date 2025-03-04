from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import db, Transaction, User, ExchangeRate, BalanceHistory
from decimal import Decimal

def calculate_total_balance_change():
    '''Calculate total balance change for the current user'''
    # Get first balance history record in last 30 days
    # Calculate total balance change
    last_month_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
    first_balance = db.session.query(BalanceHistory.amount).filter(
        BalanceHistory.user_id == current_user.id,
        BalanceHistory.symbol == current_user.settings.default_currency,
        BalanceHistory.timestamp >= last_month_timestamp,
    ).order_by(BalanceHistory.timestamp.asc()).first()

    if not first_balance:
        return 0
    
    if first_balance[0] == 0:
        return 100
    
    current_balance = current_user.get_balance(current_user.settings.default_currency)

    total_balance_change = round((current_balance - first_balance[0]) / first_balance[0] * 100, 2)

    return total_balance_change

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

    # Sum all transactions in range between last 60 and 30 days
    # Then in range between last 30 and now
    # Calculate change in %
    last_60_days_timestamp = int((datetime.now() - timedelta(days=60)).timestamp())
    last_30_days_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())

    last_60_days_earnings = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.receiver_id == current_user.id,
        Transaction.timestamp >= last_60_days_timestamp,
        Transaction.timestamp < last_30_days_timestamp,
    ).scalar() or Decimal(0.00)

    last_30_days_earnings = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.receiver_id == current_user.id,
        Transaction.timestamp >= last_30_days_timestamp,
    ).scalar() or Decimal(0.00)

    if not last_60_days_earnings or not last_30_days_earnings:
        monthly_change = 0
    elif last_60_days_earnings == 0:
        monthly_change = 100
    else:
        monthly_change = round((last_30_days_earnings - last_60_days_earnings) / last_60_days_earnings * 100, 2)

    return monthly_income, monthly_change



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

def get_all_currencies():
    '''Get all currencies'''
    all_currencies = db.session.query(ExchangeRate.symbol).all()
    all_currencies = [currency[0] for currency in all_currencies]

    return sorted(all_currencies)

def get_exchange_rate(from_currency, to_currency):
    '''Get exchange rate from one currency to another'''
    from_currency_rate = db.session.query(ExchangeRate.rate).filter_by(symbol=from_currency).scalar()
    to_currency_rate = db.session.query(ExchangeRate.rate).filter_by(symbol=to_currency).scalar()

    exchange_rate = round(to_currency_rate / from_currency_rate, 4)

    return Decimal(exchange_rate)