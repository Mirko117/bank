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
        user.add_balance(1100.00, 'EUR')
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

class TestDashboardGetPageEndpoint:
    def test_get_dashboard_shell_unauthorized(self, client):
        response = client.get('/api/dashboard/get-shell?shell=dashboard')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_get_dashboard_shell_no_shell_param(self, auth_client):
        response = auth_client.get('/api/dashboard/get-shell')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'No shell provided'

    def test_get_dashboard_shell_invalid_shell(self, auth_client):
        response = auth_client.get('/api/dashboard/get-shell?shell=invalid')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Shell not found'

    def test_get_dashboard_shell(self, auth_client):
        response = auth_client.get('/api/dashboard/get-shell?shell=dashboard')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'shell' in data

    def test_get_transactions_shell(self, auth_client):
        response = auth_client.get('/api/dashboard/get-shell?shell=transactions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'shell' in data

    def test_get_currencies_shell(self, auth_client):
        response = auth_client.get('/api/dashboard/get-shell?shell=currencies')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'shell' in data

class TestDashboardMakeQuickTransferEndpoint:
    def test_quick_transfer_unauthorized(self, client):
        response = client.post('/api/dashboard/quick-transfer')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_quick_transfer_missing_params(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient and amount required'

    def test_quick_transfer_recipient_not_found(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'nonexistent',
            'amount': '100.00'
        })
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient not found'

    def test_quick_transfer_to_self(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'testuser',
            'amount': '100.00'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Cannot transfer to yourself'

    def test_quick_transfer_invalid_amount_format(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'receiver',
            'amount': 'invalid'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_quick_transfer_negative_amount(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'receiver',
            'amount': '-100.00'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_quick_transfer_insufficient_funds(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'receiver',
            'amount': '2000.00'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Insufficient funds'

    def test_quick_transfer_more_that_1000_eur(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'receiver',
            'amount': '1001.00'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Amount must be less than 1000 EUR' in data['message']

    def test_quick_transfer_success(self, auth_client):
        response = auth_client.post('/api/dashboard/quick-transfer', data={
            'recipient': 'receiver',
            'amount': '100.00'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Transfer successful'

class TestDashboardExportTransactionsDialogEndpoint:
    def test_export_transactions_dialog_unauthorized(self, client):
        response = client.get('/api/dashboard/export-transactions-dialog')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_export_transactions_dialog_success(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions-dialog')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'html' in data
        assert 'title' in data

class TestDashboardExportTransactionsEndpoint:
    def test_export_transactions_unauthorized(self, client):
        response = client.get('/api/dashboard/export-transactions')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_export_transactions_no_file_type(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'File type required'

    def test_export_transactions_invalid_file_type(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions?file_type=invalid')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid file type'

    def test_export_transactions_xml(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions?file_type=xml')
        assert response.status_code == 200
        assert 'application/xml' in response.headers['Content-Type']
        assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.xml'

    def test_export_transactions_json(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions?file_type=json')
        assert response.status_code == 200
        assert 'application/json' in response.headers['Content-Type']
        assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.json'

    def test_export_transactions_excel(self, auth_client):
        response = auth_client.get('/api/dashboard/export-transactions?file_type=excel')
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['Content-Type']
        assert response.headers['Content-Disposition'] == 'attachment; filename=MiBank_transactions.xlsx'
        # Verify it's a valid Excel file
        pd.read_excel(io.BytesIO(response.data))

class TestDashboardAddCurrencyDialogEndpoint:
    def test_add_currency_dialog_unauthorized(self, client):
        response = client.get('/api/dashboard/add-currency-dialog')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_add_currency_dialog_success(self, auth_client):
        response = auth_client.get('/api/dashboard/add-currency-dialog')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'html' in data
        assert 'title' in data

class TestDashboardAddCurrencyEndpoint:
    def test_add_currency_unauthorized(self, client):
        response = client.post('/api/dashboard/add-currency')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_add_currency_missing_params(self, auth_client):
        response = auth_client.post('/api/dashboard/add-currency')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency required'

    def test_add_currency_invalid_currency(self, auth_client, monkeypatch):
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

    def test_add_currency_success(self, auth_client, monkeypatch):
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

class TestDashboardExchangeCurrenciesEndpointGET:
    def test_exchange_currencies_get_unauthorized(self, client):
        response = client.get('/api/dashboard/exchange-currencies')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_exchange_currencies_get_missing_params(self, auth_client):
        response = auth_client.get('/api/dashboard/exchange-currencies')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Amount, from and to currency required'

    def test_exchange_currencies_get_invalid_amount_format(self, auth_client):
        response = auth_client.get('/api/dashboard/exchange-currencies?amount=invalid&from=EUR&to=USD')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']

    def test_exchange_currencies_get_negative_amount(self, auth_client):
        response = auth_client.get('/api/dashboard/exchange-currencies?amount=-100&from=EUR&to=USD')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_exchange_currencies_get_same_currency(self, auth_client):
        response = auth_client.get('/api/dashboard/exchange-currencies?amount=100&from=EUR&to=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Cannot exchange the same currency'

    def test_exchange_currencies_get_invalid_currency(self, auth_client, monkeypatch):
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

    def test_exchange_currencies_get_insufficient_funds(self, auth_client):
        response = auth_client.get('/api/dashboard/exchange-currencies?amount=2000&from=EUR&to=USD')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Insufficient funds'

    def test_exchange_currencies_get_success(self, auth_client, monkeypatch):
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

class TestDashboardExchangeCurrenciesEndpointPOST:
    def test_exchange_currencies_post_unauthorized(self, client):
        response = client.post('/api/dashboard/exchange-currencies')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_exchange_currencies_post_missing_params(self, auth_client):
        response = auth_client.post('/api/dashboard/exchange-currencies')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Amount, from and to currency required'

    def test_exchange_currencies_post_invalid_amount_format(self, auth_client):
        response = auth_client.post('/api/dashboard/exchange-currencies', data={
            'amount': 'invalid',
            'from': 'EUR',
            'to': 'USD'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']

    def test_exchange_currencies_post_negative_amount(self, auth_client):
        response = auth_client.post('/api/dashboard/exchange-currencies', data={
            'amount': '-100',
            'from': 'EUR',
            'to': 'USD'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_exchange_currencies_post_same_currency(self, auth_client):
        response = auth_client.post('/api/dashboard/exchange-currencies', data={
            'amount': '100',
            'from': 'EUR',
            'to': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Cannot exchange the same currency'

    def test_exchange_currencies_post_invalid_currency(self, auth_client, monkeypatch):
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

    def test_exchange_currencies_post_insufficient_funds(self, auth_client):
        response = auth_client.post('/api/dashboard/exchange-currencies', data={
            'amount': '2000',
            'from': 'EUR',
            'to': 'USD'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Insufficient funds'

    def test_exchange_currencies_post_success(self, auth_client, monkeypatch):
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

# Tests for DashboardGetTransferFeeEndpoint
class TestDashboardGetTransferFeeEndpoint:
    def test_get_transfer_fee_unauthorized(self, client):
        response = client.get('/api/dashboard/get-transfer-fee')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_get_transfer_fee_missing_params(self, auth_client):
        response = auth_client.get('/api/dashboard/get-transfer-fee')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Amount required'

    def test_get_transfer_fee_missing_currency(self, auth_client):
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=100')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency required'

    def test_get_transfer_fee_invalid_amount_format(self, auth_client):
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=invalid&currency=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']

    def test_get_transfer_fee_negative_amount(self, auth_client):
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=-100&currency=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_get_transfer_fee_invalid_currency(self, auth_client, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=100&currency=GBP')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency not found'

    def test_get_transfer_fee_small_amount(self, auth_client, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')  # Same currency, rate is 1.0
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=100&currency=EUR')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['fee'] == 0  # No fee for small amounts

    def test_get_transfer_fee_large_amount(self, auth_client, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')  # Same currency, rate is 1.0
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        response = auth_client.get('/api/dashboard/get-transfer-fee?amount=1500&currency=EUR')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['fee'] == 0.005  # 0.5% fee for large amounts

# Tests for DashboardMakeTransferEndpoint
class TestDashboardMakeTransferEndpoint:
    def test_make_transfer_unauthorized(self, client):
        response = client.post('/api/dashboard/make-transfer')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_make_transfer_missing_params(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient, amount and currency required'

    def test_make_transfer_recipient_not_found(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'nonexistent',
            'amount': '100.00',
            'currency': 'EUR'
        })
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient not found'

    def test_make_transfer_to_self(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': '100.00',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Cannot transfer to yourself'

    def test_make_transfer_invalid_currency(self, auth_client, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': '100.00',
            'currency': 'GBP'
        })
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency not found'

    def test_make_transfer_invalid_amount_format(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': 'invalid',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']

    def test_make_transfer_negative_amount(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': '-100.00',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount' in data['message']

    def test_make_transfer_insufficient_funds(self, auth_client):
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': '2000.00',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Insufficient funds'

    def test_make_transfer_success(self, auth_client, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': '100.00',
            'currency': 'EUR',
            'description': 'Test transfer'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Transfer successful'

    def test_make_transfer_with_fee(self, auth_client, app, monkeypatch):
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == 'EUR' and to_curr == 'EUR':
                return Decimal('1.0')
            else:
                return Decimal('0.9')
        
        from app.api import routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        # Get initial balances
        with app.app_context():
            sender = User.query.filter_by(username='testuser').first()
            receiver = User.query.filter_by(username='receiver').first()
            sender_initial = float(sender.get_balance('EUR'))
            receiver_initial = float(receiver.get_balance('EUR') or 0)
        
        # Make a transfer of 500 EUR which should incur a fee
        response = auth_client.post('/api/dashboard/make-transfer', data={
            'recipient': 'receiver',
            'amount': '500.00',
            'currency': 'EUR',
            'description': 'Test transfer with fee'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Check balances after transfer
        with app.app_context():
            sender = User.query.filter_by(username='testuser').first()
            receiver = User.query.filter_by(username='receiver').first()
            sender_after = float(sender.get_balance('EUR'))
            receiver_after = float(receiver.get_balance('EUR') or 0)
            
            # Verify the sender was charged the full amount plus fee
            assert sender_initial - sender_after == 500.00
            
            # Verify the receiver got the amount (without the fee)
            assert receiver_after - receiver_initial == 500.00

class TestDashboardSavePersonalInfoEndpoint:
    def test_save_personal_info_unauthorized(self, client):
        response = client.patch('/api/dashboard/save-personal-info')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_save_personal_info_missing_params(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-personal-info')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'All fields are required'

    def test_save_personal_info_invalid_name_length(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'ab',  # Too short
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'must be at least 3 characters' in data['message']

    def test_save_personal_info_name_with_numbers(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'Test1',  # Contains number
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Name cannot contain numbers'

    def test_save_personal_info_invalid_email(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'invalid-email'  # Invalid email format
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid email'

    def test_save_personal_info_existing_username(self, auth_client, app):
        # Create another user with a different username
        with app.app_context():
            another_user = User(
                username='anotheruser',
                first_name='Another',
                last_name='User',
                email='another@example.com',
                role='user'
            )
            another_user.set_password('password')
            db.session.add(another_user)
            db.session.commit()
        
        # Try to change to the existing username
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'anotheruser',  # Already exists
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Username already exists'

    def test_save_personal_info_existing_email(self, auth_client, app):
        # Create another user with a different email
        with app.app_context():
            if not User.query.filter_by(email='another@example.com').first():
                another_user = User(
                    username='anotheruser',
                    first_name='Another',
                    last_name='User',
                    email='another@example.com',
                    role='user'
                )
                another_user.set_password('password')
                db.session.add(another_user)
                db.session.commit()
        
        # Try to change to the existing email
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'another@example.com'  # Already exists
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Email already exists'

    def test_save_personal_info_success(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-personal-info', data={
            'first_name': 'Updated',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Personal info updated'

class TestDashboardChangePasswordEndpoint:
    def test_change_password_unauthorized(self, client):
        response = client.patch('/api/dashboard/change-password')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_change_password_missing_params(self, auth_client):
        response = auth_client.patch('/api/dashboard/change-password')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'All fields are required'

    def test_change_password_not_matching(self, auth_client):
        response = auth_client.patch('/api/dashboard/change-password', data={
            'current_password': 'password',
            'new_password': 'newpass123',
            'confirm_password': 'newpass456'  # Doesn't match new password
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Passwords do not match'

    def test_change_password_too_short(self, auth_client):
        response = auth_client.patch('/api/dashboard/change-password', data={
            'current_password': 'password',
            'new_password': 'pass1',  # Too short
            'confirm_password': 'pass1'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Password must be at least 6 characters long'

    def test_change_password_no_numbers(self, auth_client):
        response = auth_client.patch('/api/dashboard/change-password', data={
            'current_password': 'password',
            'new_password': 'newpassword',  # No numbers
            'confirm_password': 'newpassword'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Password must contain at least one number'

    def test_change_password_incorrect_current(self, auth_client):
        response = auth_client.patch('/api/dashboard/change-password', data={
            'current_password': 'wrongpassword',  # Incorrect current password
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid current password'

    def test_change_password_success(self, auth_client, app):
        response = auth_client.patch('/api/dashboard/change-password', data={
            'current_password': 'password',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Password changed'
        
        # Verify the password was actually changed
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user.check_password('newpass123')

class TestDashboardSaveSettingsEndpoint:
    def test_save_settings_unauthorized(self, client):
        response = client.patch('/api/dashboard/save-settings')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'

    def test_save_settings_missing_params(self, auth_client):
        response = auth_client.patch('/api/dashboard/save-settings')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'All fields are required'

    def test_save_settings_invalid_language(self, auth_client, monkeypatch):
        def mock_check_language(language):
            return language in ['en', 'sl']
        
        from app.api import routes
        monkeypatch.setattr(routes, 'check_language', mock_check_language)
        
        response = auth_client.patch('/api/dashboard/save-settings', data={
            'language': 'invalid',  # Invalid language
            'default_currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid language'

    def test_save_settings_invalid_currency(self, auth_client, monkeypatch):
        def mock_check_language(language):
            return language in ['en', 'sl']
        
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import routes
        monkeypatch.setattr(routes, 'check_language', mock_check_language)
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = auth_client.patch('/api/dashboard/save-settings', data={
            'language': 'en',
            'default_currency': 'GBP'  # Invalid currency
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Invalid currency'

    def test_save_settings_success(self, auth_client, app, monkeypatch):
        def mock_check_language(language):
            return language in ['en', 'sl']
        
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import routes
        monkeypatch.setattr(routes, 'check_language', mock_check_language)
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        # First ensure settings exist for the user
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            if not hasattr(user, 'settings') or user.settings is None:
                from app.models import Settings
                settings = Settings(user_id=user.id, language='en', default_currency='EUR')
                db.session.add(settings)
                db.session.commit()
        
        response = auth_client.patch('/api/dashboard/save-settings', data={
            'language': 'sl',
            'default_currency': 'USD'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Settings updated'
        
        # Verify settings were updated
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user.settings.language == 'sl'
            assert user.settings.default_currency == 'USD'
