from flask import current_app, session
from flask_login import current_user
from app.models import db, ExchangeRate, ExchangeRateLastUpdate
from datetime import datetime
import requests
import time
import json
import os
import re


def load_language(lang:str):
    '''Load language file'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_language(lang:str):
    '''Check if language file exists'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    return os.path.exists(filepath)

def get_translations():
    '''Get translations'''
    lang = session.get('lang', 'en') # Default to English
    return load_language(lang)

def get_user_translations():
    '''Get translations for current user'''
    lang = current_user.settings.language
    if not check_language(lang):
        lang = 'en'
    return load_language(lang)

def is_valid_number_format(s):
    '''Check if a string is a valid number format'''
    # Regular expression to match numbers with only one comma or period
    pattern = r'^\d+(?:[.,]\d{1,2})?$'
    return bool(re.match(pattern, s))

def format_money(value, decimals=2):
    '''Format a number as money'''
    return f"{value:,.{decimals}f}"

def unix_to_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    '''Convert timestamp to datetime and format it'''
    return datetime.fromtimestamp(value).strftime(format)

def update_exchange_rates():
    '''Update exchange rates in the database'''

    # Check if 1h has passed since the last update
    last_update = ExchangeRateLastUpdate.query.first()
    if last_update:
        if int(time.time()) - int(last_update.timestamp) < 3600:
            return False

    # Get the latest exchange rates from the API
    response = requests.get(f'https://v6.exchangerate-api.com/v6/{current_app.config["EXCHANGE_RATE_API_KEY"]}/latest/EUR')
    data = response.json()

    # Check if the response is successful
    if data['result'] == 'success':
        # Get the rates from the response
        rates = data['conversion_rates']

        # Update/add time of last update if 1h has passed
        if last_update:
                last_update.timestamp = int(time.time())
        else:
            last_update = ExchangeRateLastUpdate()
            db.session.add(last_update)

        # Update/add exchange rates
        for symbol, rate in rates.items():
            exchange_rate = ExchangeRate.query.filter_by(symbol=symbol).first()
            if exchange_rate:
                exchange_rate.rate = rate
            else:
                exchange_rate = ExchangeRate(symbol=symbol, rate=rate)
                db.session.add(exchange_rate)

        db.session.commit()
        return True
    
    return False
