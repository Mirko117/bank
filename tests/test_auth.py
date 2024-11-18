from app import create_app, db
from app.models import User
import pytest

# Create a test app instance
app = create_app(config_object='config.TestingConfig')

@pytest.fixture(scope='session')
def client():
    # Create the database and the database tables, then delete them after the test
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()

### Registration tests ###

def test_register_success(client):
    # Test a successful registration
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 201
    assert response.json['status'] == 'User created successfully, please check your email for username'

def test_register_empty_name(client):
    # Test registration with an empty name
    response = client.post('/auth/register', data={
        'name': '',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Name is required'

def test_register_invalid_name(client):
    # Test registration with an invalid name
    response = client.post('/auth/register', data={
        'name': 'Jo',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Name is too short'

def test_register_invalid_name_with_number(client):
    # Test registration with an invalid name
    response = client.post('/auth/register', data={
        'name': 'Jo1',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Name must not contain a number'

def test_register_empty_surname(client):
    # Test registration with an empty surname
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': '',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Surname is required'

def test_register_invalid_surname(client):
    # Test registration with an invalid surname
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Do',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Surname is too short'

def test_register_invalid_surname_with_number(client):
    # Test registration with an invalid surname
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Do1',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Surname must not contain a number'

def test_register_empty_email(client):
    # Test registration with an empty email
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': '',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Email is required'

def test_register_invalid_email(client):
    # Test registration with an invalid email
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doeexample.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Invalid email'

def test_register_empty_password(client):
    # Test registration with an empty password
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': '',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Password is required'

def test_register_password_mismatch(client):
    # Test registration with password mismatch
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password1234'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Passwords do not match'

def test_register_password_without_number(client):
    # Test registration with password without a number
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Password must contain a number'

def test_register_existing_email(client):
    # Test registration with an existing email
    response = client.post('/auth/register', data={
        'name': 'John',
        'surname': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123',
        'confirm-password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Email already exists'


## Login tests ###

def test_login_empty_username(client):
    global username
    # Test login with an empty username
    # Get the username of the user we created in the previous test
    with app.app_context():
        user = User.query.filter_by(email='john.doe@example.com').first()
        assert user is not None
        username = user.username
    
    response = client.post('/auth/login', data={
        'username': '',
        'password': 'Password123'
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Username is required'

def test_login_empty_password(client):
    # Test login with an empty password
    response = client.post('/auth/login', data={
        'username': 'Username',
        'password': ''
    })
    assert response.status_code == 400
    assert response.json['status'] == 'Password is required'

def test_login_invalid_username(client):
    # Test login with invalid credentials
    response = client.post('/auth/login', data={
        'username': 'InvalidUsername',
        'password': 'Password123'
    })
    assert response.status_code == 401
    assert response.json['status'] == 'Invalid credentials'

def test_login_invalid_password(client):
    # Test login with invalid credentials
    response = client.post('/auth/login', data={
        'username': username,
        'password': 'Password12'
    })
    assert response.status_code == 401
    assert response.json['status'] == 'Invalid credentials'

def test_login_success(client):
    # Test a successful login
    response = client.post('/auth/login', data={
        'username': username,
        'password': 'Password123'
    })
    assert response.status_code == 200
    assert response.json['status'] == 'Logged in successfully'