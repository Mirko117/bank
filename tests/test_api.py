from decimal import Decimal
from app import create_app, db
from app.models import User, Transaction, Balance, ExchangeRate
from flask_login import login_user
from config import TestingConfig
import pytest
import json
import pandas as pd
import io

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        
        # Create a test user
        user = User(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role='user'
        )
        user.set_password('password')
        db.session.add(user)
        
        # Create another user for transfers
        receiver = User(
            username='receiver',
            first_name='Receive',
            last_name='User',
            email='receiver@example.com',
            role='user'
        )
        receiver.set_password('password')
        db.session.add(receiver)
        
        # Add balances
        user.add_balance(1000.00, 'EUR')
        user.add_balance(500.00, 'USD')
        
        # Add exchange rates
        rate1 = ExchangeRate(symbol='EUR', rate=1.0)
        rate2 = ExchangeRate(symbol='USD', rate=0.9)
        db.session.add(rate1)
        db.session.add(rate2)

        db.session.commit()
        
        yield app
        
        # Clean up at the end of test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(app, client):
    with app.test_request_context():
        user = User.query.filter_by(username='testuser').first()
        login_user(user)
        
        # Create a session cookie
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True
            
    return client

# Test DashboardGetPageEndpoint
def test_get_dashboard_shell_unauthorized(client):
    response = client.get('/api/dashboard/get-shell?shell=dashboard')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_get_dashboard_shell_no_shell_param(auth_client):
    response = auth_client.get('/api/dashboard/get-shell')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'No shell provided'

def test_get_dashboard_shell_invalid_shell(auth_client):
    response = auth_client.get('/api/dashboard/get-shell?shell=invalid')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Shell not found'

def test_get_dashboard_shell(auth_client):
    response = auth_client.get('/api/dashboard/get-shell?shell=dashboard')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'shell' in data

def test_get_transactions_shell(auth_client):
    response = auth_client.get('/api/dashboard/get-shell?shell=transactions')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'shell' in data

def test_get_currencies_shell(auth_client):
    response = auth_client.get('/api/dashboard/get-shell?shell=currencies')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'shell' in data

# Test DashboardMakeQuickTransferEndpoint
def test_quick_transfer_unauthorized(client):
    response = client.post('/api/dashboard/quick-transfer')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_quick_transfer_missing_params(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Recipient and amount required'

def test_quick_transfer_recipient_not_found(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'nonexistent',
        'amount': '100.00'
    })
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Recipient not found'

def test_quick_transfer_to_self(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'testuser',
        'amount': '100.00'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Cannot transfer to yourself'

def test_quick_transfer_invalid_amount_format(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'receiver',
        'amount': 'invalid'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount' in data['message']

def test_quick_transfer_negative_amount(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'receiver',
        'amount': '-100.00'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount' in data['message']

def test_quick_transfer_insufficient_funds(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'receiver',
        'amount': '2000.00'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Insufficient funds'

def test_quick_transfer_success(auth_client):
    response = auth_client.post('/api/dashboard/quick-transfer', data={
        'recipient': 'receiver',
        'amount': '100.00'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['message'] == 'Transfer successful'

# Test DashboardExportTransactionsDialogEndpoint
def test_export_transactions_dialog_unauthorized(client):
    response = client.get('/api/dashboard/export-transactions-dialog')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_export_transactions_dialog_success(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions-dialog')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'html' in data
    assert 'title' in data

# Test DashboardExportTransactionsEndpoint
def test_export_transactions_unauthorized(client):
    response = client.get('/api/dashboard/export-transactions')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_export_transactions_no_file_type(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'File type required'

def test_export_transactions_invalid_file_type(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions?file_type=invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Invalid file type'

def test_export_transactions_xml(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions?file_type=xml')
    assert response.status_code == 200
    assert 'application/xml' in response.headers['Content-Type']
    assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.xml'

def test_export_transactions_json(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions?file_type=json')
    assert response.status_code == 200
    assert 'application/json' in response.headers['Content-Type']
    assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.json'

def test_export_transactions_excel(auth_client):
    response = auth_client.get('/api/dashboard/export-transactions?file_type=excel')
    assert response.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['Content-Type']
    assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.xlsx'
    # Verify it's a valid Excel file
    pd.read_excel(io.BytesIO(response.data))

# Test DashboardAddCurrencyDialogEndpoint
def test_add_currency_dialog_unauthorized(client):
    response = client.get('/api/dashboard/add-currency-dialog')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_add_currency_dialog_success(auth_client):
    response = auth_client.get('/api/dashboard/add-currency-dialog')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'html' in data
    assert 'title' in data

# Test DashboardAddCurrencyEndpoint
def test_add_currency_unauthorized(client):
    response = client.post('/api/dashboard/add-currency')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_add_currency_missing_params(auth_client):
    response = auth_client.post('/api/dashboard/add-currency')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Currency required'

def test_add_currency_invalid_currency(auth_client, monkeypatch):
    # Mock the get_new_currencies function to return a specific list
    def mock_get_new_currencies():
        return ['GBP']
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_new_currencies', mock_get_new_currencies)
    
    response = auth_client.post('/api/dashboard/add-currency', data={
        'currency': 'INVALID'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Invalid currency'

def test_add_currency_success(auth_client, monkeypatch):
    # Mock the get_new_currencies function to return a specific list
    def mock_get_new_currencies():
        return ['GBP']
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_new_currencies', mock_get_new_currencies)
    
    response = auth_client.post('/api/dashboard/add-currency', data={
        'currency': 'GBP'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['message'] == 'Currency added'

# Test DashboardExchangeCurrenciesEndpoint - GET
def test_exchange_currencies_get_unauthorized(client):
    response = client.get('/api/dashboard/exchange-currencies')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_exchange_currencies_get_missing_params(auth_client):
    response = auth_client.get('/api/dashboard/exchange-currencies')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Amount, from and to currency required'

def test_exchange_currencies_get_invalid_amount_format(auth_client):
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=invalid&from=EUR&to=USD')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount format' in data['message']

def test_exchange_currencies_get_negative_amount(auth_client):
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=-100&from=EUR&to=USD')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount' in data['message']

def test_exchange_currencies_get_same_currency(auth_client):
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=100&from=EUR&to=EUR')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Cannot exchange the same currency'

def test_exchange_currencies_get_invalid_currency(auth_client, monkeypatch):
    # Mock the get_all_currencies function to return a specific list
    def mock_get_all_currencies():
        return ['EUR', 'USD']
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_all_currencies', mock_get_all_currencies)
    
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=100&from=EUR&to=INVALID')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Invalid currency'

def test_exchange_currencies_get_insufficient_funds(auth_client):
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=2000&from=EUR&to=USD')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Insufficient funds'

def test_exchange_currencies_get_success(auth_client, monkeypatch):
    # Mock the get_all_currencies function
    def mock_get_all_currencies():
        return ['EUR', 'USD']
    
    # Mock the get_exchange_rate function
    def mock_get_exchange_rate(from_curr, to_curr):
        return Decimal('0.9')
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_all_currencies', mock_get_all_currencies)
    monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
    
    response = auth_client.get('/api/dashboard/exchange-currencies?amount=100&from=EUR&to=USD')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'exchange_rate' in data
    assert 'result' in data

# Test DashboardExchangeCurrenciesEndpoint - POST
def test_exchange_currencies_post_unauthorized(client):
    response = client.post('/api/dashboard/exchange-currencies')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Unauthorized'

def test_exchange_currencies_post_missing_params(auth_client):
    response = auth_client.post('/api/dashboard/exchange-currencies')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Amount, from and to currency required'

def test_exchange_currencies_post_invalid_amount_format(auth_client):
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': 'invalid',
        'from': 'EUR',
        'to': 'USD'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount format' in data['message']

def test_exchange_currencies_post_negative_amount(auth_client):
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': '-100',
        'from': 'EUR',
        'to': 'USD'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid amount' in data['message']

def test_exchange_currencies_post_same_currency(auth_client):
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': '100',
        'from': 'EUR',
        'to': 'EUR'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Cannot exchange the same currency'

def test_exchange_currencies_post_invalid_currency(auth_client, monkeypatch):
    # Mock the get_all_currencies function
    def mock_get_all_currencies():
        return ['EUR', 'USD']
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_all_currencies', mock_get_all_currencies)
    
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': '100',
        'from': 'EUR',
        'to': 'INVALID'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Invalid currency'

def test_exchange_currencies_post_insufficient_funds(auth_client):
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': '2000',
        'from': 'EUR',
        'to': 'USD'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['message'] == 'Insufficient funds'

def test_exchange_currencies_post_success(auth_client, monkeypatch):
    # Mock the get_all_currencies function
    def mock_get_all_currencies():
        return ['EUR', 'USD']
    
    # Mock the get_exchange_rate function
    def mock_get_exchange_rate(from_curr, to_curr):
        return Decimal('0.9')
    
    from app.api import routes
    monkeypatch.setattr(routes, 'get_all_currencies', mock_get_all_currencies)
    monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
    
    response = auth_client.post('/api/dashboard/exchange-currencies', data={
        'amount': '100',
        'from': 'EUR',
        'to': 'USD'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['message'] == 'Exchange successful'
