from decimal import Decimal
from app import create_app, db
from app.models import User, Transaction, ExchangeRate
from flask_login import login_user
from config import TestingConfig
import pytest
import json

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin = User(
            username='adminuser',
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('password')
        db.session.add(admin)
        
        # Create a regular user
        user = User(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role='user'
        )
        user.set_password('password')
        db.session.add(user)
        
        # Add balances
        admin.add_balance(10000.00, 'EUR')
        admin.add_balance(5000.00, 'USD')
        user.add_balance(1000.00, 'EUR')
        
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
            # Add Flask-Login specific key
            session['_user_id'] = user.id
            
    return client

@pytest.fixture
def admin_client(app, client):
    with app.test_request_context():
        admin = User.query.filter_by(username='adminuser').first()
        login_user(admin)
        
        # Create a session cookie
        with client.session_transaction() as session:
            session['user_id'] = admin.id
            session['_fresh'] = True
            # Add Flask-Login specific key
            session['_user_id'] = admin.id
            
    return client

class TestAdminDashboardGetPageEndpoint:
    def test_get_admin_shell_unauthorized(self, client):
        """Test that unauthorized users cannot access admin shells"""
        response = client.get('/api/admin-dashboard/get-shell?shell=admin-transfers')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_admin_shell_regular_user(self, auth_client):
        """Test that regular users cannot access admin shells"""
        response = auth_client.get('/api/admin-dashboard/get-shell?shell=admin-transfers')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_admin_shell_no_shell_param(self, admin_client):
        """Test that shell parameter is required"""
        response = admin_client.get('/api/admin-dashboard/get-shell')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'No shell provided'
    
    def test_get_admin_shell_invalid_shell(self, admin_client):
        """Test with invalid shell parameter"""
        response = admin_client.get('/api/admin-dashboard/get-shell?shell=invalid')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Shell not found'
    
    def test_get_admin_transfers_shell(self, admin_client):
        """Test getting admin transfers shell"""
        response = admin_client.get('/api/admin-dashboard/get-shell?shell=admin-transfers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'shell' in data
    
    def test_get_admin_user_transactions_shell(self, admin_client):
        """Test getting admin user transactions shell"""
        response = admin_client.get('/api/admin-dashboard/get-shell?shell=admin-user-transactions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'shell' in data

class TestAdminDashboardGetUserTransactionsTableEndpoint:
    def test_get_user_transactions_table_unauthorized(self, client):
        """Test that unauthorized users cannot access user transactions"""
        response = client.get('/api/admin-dashboard/get-user-transactions-table?username=testuser')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_user_transactions_table_regular_user(self, auth_client):
        """Test that regular users cannot access user transactions"""
        response = auth_client.get('/api/admin-dashboard/get-user-transactions-table?username=testuser')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_user_transactions_table_no_username(self, admin_client):
        """Test that username parameter is required"""
        response = admin_client.get('/api/admin-dashboard/get-user-transactions-table')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Usernmae required'  # Note: There's a typo in your API
    
    def test_get_user_transactions_table_invalid_username(self, admin_client):
        """Test with invalid username parameter"""
        response = admin_client.get('/api/admin-dashboard/get-user-transactions-table?username=nonexistentuser')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'User not found'
    
    def test_get_user_transactions_table_success(self, admin_client, app):
        """Test getting user transactions table successfully"""
        with app.app_context():
            # Add some transactions for the test user
            user = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='adminuser').first()
            
            # Create a transaction
            transaction = Transaction(
                name="Test Transaction",
                user_id=admin.id,
                receiver_id=user.id,
                amount=100.00,
                currency='EUR',
                status='success',
                transaction_type='transfer',
                description='Test transaction'
            )
            db.session.add(transaction)
            db.session.commit()
        
        response = admin_client.get('/api/admin-dashboard/get-user-transactions-table?username=testuser')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'table' in data

class TestAdminDashboardGetTransferFeeEndpoint:
    def test_get_transfer_fee_unauthorized(self, client):
        """Test that unauthorized users cannot access transfer fee"""
        response = client.get('/api/admin-dashboard/get-transfer-fee?amount=1000&currency=EUR')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_transfer_fee_regular_user(self, auth_client):
        """Test that regular users cannot access transfer fee"""
        response = auth_client.get('/api/admin-dashboard/get-transfer-fee?amount=1000&currency=EUR')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_get_transfer_fee_no_amount(self, admin_client):
        """Test that amount parameter is required"""
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?currency=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Amount required'
    
    def test_get_transfer_fee_invalid_amount(self, admin_client):
        """Test with invalid amount parameter"""
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=invalid&currency=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']
    
    def test_get_transfer_fee_negative_amount(self, admin_client):
        """Test with negative amount parameter"""
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=-100&currency=EUR')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']
        # It should be:
        # assert data['message'] == 'Invalid amount'
        # but when it checks format, that - sign is not allowed
        # Invalid amount is there just in case if it passes the format check
    
    def test_get_transfer_fee_no_currency(self, admin_client):
        """Test that currency parameter is required"""
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=1000')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency required'
    
    def test_get_transfer_fee_invalid_currency(self, admin_client, monkeypatch):
        """Test with invalid currency parameter"""
        # Mock the get_user_currencies function to return a specific list
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=1000&currency=INVALID')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency not found'
    
    def test_get_transfer_fee_small_amount(self, admin_client, monkeypatch):
        """Test calculating fee for small amount (should be 0)"""
        # Mock the get_exchange_rate and get_user_currencies functions
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')
        
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=500&currency=EUR')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['fee'] == 0
    
    def test_get_transfer_fee_large_amount(self, admin_client, monkeypatch):
        """Test calculating fee for large amount (should be 0.5%)"""
        # Mock the get_exchange_rate and get_user_currencies functions
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')
        
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = admin_client.get('/api/admin-dashboard/get-transfer-fee?amount=2000&currency=EUR')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['fee'] == 0.005

class TestAdminDashboardMakeTransferEndpoint:
    def test_make_transfer_unauthorized(self, client):
        """Test that unauthorized users cannot make transfers"""
        response = client.post('/api/admin-dashboard/make-transfer')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_make_transfer_regular_user(self, auth_client):
        """Test that regular users cannot make admin transfers"""
        response = auth_client.post('/api/admin-dashboard/make-transfer')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Unauthorized'
    
    def test_make_transfer_missing_params(self, admin_client):
        """Test that required parameters are validated"""
        response = admin_client.post('/api/admin-dashboard/make-transfer')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient, amount and currency required'
    
    def test_make_transfer_recipient_not_found(self, admin_client):
        """Test transfer to non-existent recipient"""
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'nonexistentuser',
            'amount': '100',
            'currency': 'EUR'
        })
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Recipient not found'
    
    def test_make_transfer_to_self(self, admin_client):
        """Test transfer to self (should fail)"""
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'adminuser',
            'amount': '100',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Cannot transfer to yourself'
    
    def test_make_transfer_invalid_currency(self, admin_client, monkeypatch):
        """Test transfer with invalid currency"""
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': '100',
            'currency': 'INVALID'
        })
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['message'] == 'Currency not found'
    
    def test_make_transfer_invalid_amount_format(self, admin_client):
        """Test transfer with invalid amount format"""
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': 'invalid',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']
    
    def test_make_transfer_negative_amount(self, admin_client):
        """Test transfer with negative amount"""
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': '-100',
            'currency': 'EUR'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid amount format' in data['message']
    
    def test_make_transfer_success_without_fee(self, admin_client, app, monkeypatch):
        """Test successful transfer without fee"""
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        # Check initial balances
        with app.app_context():
            recipient = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='adminuser').first()
            
            initial_recipient_balance = recipient.get_balance('EUR')
            initial_admin_balance = admin.get_balance('EUR')
        
        # Make the transfer
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': '500',
            'currency': 'EUR',
            'description': 'Test transfer'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Transfer successful'
        
        # Check updated balances
        with app.app_context():
            recipient = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='adminuser').first()
            
            # Verify balances changed correctly
            assert recipient.get_balance('EUR') == initial_recipient_balance + 500
            
            # Check transaction was created
            transaction = Transaction.query.filter_by(description='Test transfer').first()
            assert transaction is not None
            assert transaction.amount == 500
            assert transaction.fee == 0
            assert transaction.currency == 'EUR'
    
    def test_make_transfer_success_with_fee(self, admin_client, app, monkeypatch):
        """Test successful transfer with fee"""
        def mock_get_user_currencies():
            return ['EUR', 'USD']
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return Decimal('1.0')
        
        from app.api import admin_dashboard_routes as routes
        monkeypatch.setattr(routes, 'get_user_currencies', mock_get_user_currencies)
        monkeypatch.setattr(routes, 'get_exchange_rate', mock_get_exchange_rate)
        
        # Check initial balances
        with app.app_context():
            recipient = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='adminuser').first()
            
            initial_recipient_balance = recipient.get_balance('EUR')
            initial_admin_balance = admin.get_balance('EUR')
        
        # Make the transfer (large enough to trigger fee)
        response = admin_client.post('/api/admin-dashboard/make-transfer', data={
            'recipient': 'testuser',
            'amount': '2000',
            'currency': 'EUR',
            'description': 'Test transfer with fee'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Transfer successful'
        
        # Check updated balances
        with app.app_context():
            recipient = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='adminuser').first()
            
            # Verify recipient received amount minus fee
            expected_amount = Decimal('2000') * Decimal('0.995')
            assert round(recipient.get_balance('EUR') - initial_recipient_balance, 2) == round(expected_amount, 2)
            
            # Check transaction was created with fee
            transaction = Transaction.query.filter_by(description='Test transfer with fee').first()
            assert transaction is not None
            assert round(transaction.amount, 2) == round(expected_amount, 2)
            assert round(transaction.fee, 2) == round(Decimal('2000') * Decimal('0.005'), 2)
            assert transaction.currency == 'EUR'