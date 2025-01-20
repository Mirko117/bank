from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import db, Transaction, User


def calculate_monthly_income_and_change():
    '''Calculate monthly income and change for the current user'''
    # Set timestamp for 30 days ago
    last_month_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())

    # Calculate monthly earnings and expenses
    monthly_earnings = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.receiver_id == current_user.id,
        Transaction.timestamp >= last_month_timestamp,
    ).scalar() or 0
    monthly_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.timestamp >= last_month_timestamp,
    ).scalar() or 0

    # Calculate monthly income
    monthly_income = round(monthly_earnings - monthly_expenses, 2)

    return monthly_income


