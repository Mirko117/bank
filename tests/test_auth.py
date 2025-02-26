from app import create_app, db
from app.models import User
from config import TestingConfig
import pytest

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing"""
    app = create_app(TestingConfig)
    return app

@pytest.fixture(scope='session')
def test_client(app):
    """Create a test client for the app"""
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def registered_user(test_client, app):
    """Create a test user that can be reused across tests"""
    user_data = {
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    }
    
    test_client.post('/auth/register', data=user_data)
    
    with app.app_context():
        user = User.query.filter_by(email=user_data['email']).first()
        return {'username': user.username, 'email': user.email, 'password': 'Password123'}

class TestRegistration:
    """Tests for the registration functionality"""
    
    def test_register_success(self, test_client):
        """Test successful registration with valid data"""
        response = test_client.post('/auth/register', data={
            'name': 'Jane',
            'surname': 'Smith',
            'email': 'jane.smith@example.com',
            'password': 'Password123',
            'confirm-password': 'Password123'
        })
        assert response.status_code == 201

        # Original code:
        # assert response.json['status'] == 'User created successfully, please check your email for username'
        # Changed it because there is +username in the response rn for testing purposes
        # This will be removed in production
        assert 'User created successfully, please check your email for username' in response.json['status'] 
    
    @pytest.mark.parametrize('field, value, status_code, message', [
        ('name', '', 400, 'Name is required'),
        ('name', 'Jo', 400, 'Name is too short'),
        ('name', 'Jo1', 400, 'Name must not contain a number'),
        ('surname', '', 400, 'Surname is required'),
        ('surname', 'Do', 400, 'Surname is too short'),
        ('surname', 'Do1', 400, 'Surname must not contain a number'),
        ('email', '', 400, 'Email is required'),
        ('email', 'john.doeexample.com', 400, 'Invalid email'),
        ('password', '', 400, 'Password is required'),
        ('password', 'Password', 400, 'Password must contain a number'),
    ])
    def test_register_invalid_fields(self, test_client, field, value, status_code, message):
        """Test registration with various invalid inputs"""
        data = {
            'name': 'John',
            'surname': 'Doe',
            'email': 'new.user@example.com',
            'password': 'Password123',
            'confirm-password': 'Password123'
        }
        # Override the specified field with the test value
        data[field] = value
        
        response = test_client.post('/auth/register', data=data)
        assert response.status_code == status_code
        assert response.json['status'] == message
    
    def test_register_password_mismatch(self, test_client):
        """Test registration with mismatched passwords"""
        response = test_client.post('/auth/register', data={
            'name': 'John',
            'surname': 'Doe',
            'email': 'another.user@example.com',
            'password': 'Password123',
            'confirm-password': 'Password1234'
        })
        assert response.status_code == 400
        assert response.json['status'] == 'Passwords do not match'
    
    def test_register_existing_email(self, test_client, registered_user):
        """Test registration with an email that already exists"""
        response = test_client.post('/auth/register', data={
            'name': 'Different',
            'surname': 'Person',
            'email': registered_user['email'],
            'password': 'Password123',
            'confirm-password': 'Password123'
        })
        assert response.status_code == 400
        assert response.json['status'] == 'Email already exists'


class TestLogin:
    """Tests for the login functionality"""
    
    @pytest.mark.parametrize('field, value, status_code, message', [
        ('username', '', 400, 'Username is required'),
        ('password', '', 400, 'Password is required'),
    ])
    def test_login_empty_fields(self, test_client, field, value, status_code, message):
        """Test login with empty required fields"""
        data = {'username': 'someusername', 'password': 'Password123'}
        data[field] = value
        
        response = test_client.post('/auth/login', data=data)
        assert response.status_code == status_code
        assert response.json['status'] == message
    
    def test_login_invalid_username(self, test_client):
        """Test login with an invalid username"""
        response = test_client.post('/auth/login', data={
            'username': 'InvalidUsername',
            'password': 'Password123'
        })
        assert response.status_code == 401
        assert response.json['status'] == 'Invalid credentials'
    
    def test_login_invalid_password(self, test_client, registered_user):
        """Test login with an invalid password"""
        response = test_client.post('/auth/login', data={
            'username': registered_user['username'],
            'password': 'WrongPassword123'
        })
        assert response.status_code == 401
        assert response.json['status'] == 'Invalid credentials'
    
    def test_login_success(self, test_client, registered_user):
        """Test successful login with valid credentials"""
        response = test_client.post('/auth/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        assert response.status_code == 200
        assert response.json['status'] == 'Logged in successfully'