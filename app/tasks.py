from celery import shared_task
from app import db
from app.models import ExchangeRate, ExchangeRateLastUpdate
import variables
import requests
import time


@shared_task
def update_exchange_rates():
    '''Update exchange rates in the database'''

    # Check if 1h has passed since the last update
    last_update = ExchangeRateLastUpdate.query.first()
    if last_update:
        if int(time.time()) - int(last_update.timestamp) < 3600:
            return False

    # Get the latest exchange rates from the API
    response = requests.get(f'https://v6.exchangerate-api.com/v6/{variables.EXCHANGE_RATE_API_KEY}/latest/EUR')
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
