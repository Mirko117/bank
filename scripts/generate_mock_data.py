import sys
from pathlib import Path

# This runs script from the project root directory
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from faker import Faker
from random import choice, randint, uniform
from app import db, create_app
from app.models import User, Transaction, Card, Log

fake = Faker()

def generate_users(num_users=100):
    users = []
    with open("scripts/users_and_passwords.txt", "w") as file:
        file.write("Generated Users and Passwords\n")
        file.write("=" * 30 + "\n")
        
        for _ in range(num_users):
            password = fake.password(length=12)
            user = User(
                username=fake.unique.user_name(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                role="user",
                created_at=int(fake.date_time_between(start_date='-1y', end_date='now').timestamp()),
            )
            user.set_password(password)
            db.session.add(user)
            users.append(user)

            # Save to text file
            file.write(f"Username: {user.username}\n")
            file.write(f"Email: {user.email}\n")
            file.write(f"Password: {password}\n")
            file.write("-" * 30 + "\n")
        
    db.session.commit()
    return users

def generate_balances(users):
    for user in users:
        user.add_balance(round(uniform(100, 20000), 2), "EUR")
    db.session.commit()

def generate_transactions(users, num_transactions=1000):
    for _ in range(num_transactions):
        sender = choice(users)
        receiver = choice(users)
        while sender.id == receiver.id:
            receiver = choice(users)
        
        transaction = Transaction(
            name=choice(['Netflix', 'Spotify', 'Amazon', 'Bank Transfer']),
            user_id=sender.id,
            receiver_id=receiver.id,
            amount=round(uniform(1, 1000), 2),
            currency="EUR",
            status=choice(['pending', 'success', 'failed']),
            transaction_type=choice(['deposit', 'withdrawal', 'transfer']),
            description=fake.sentence(),
            timestamp=int(fake.date_time_between(start_date='-3M', end_date='now').timestamp()),
        )
        db.session.add(transaction)
    db.session.commit()

def generate_cards(users, num_cards=200):
    for _ in range(num_cards):
        user = choice(users)
        card = Card(
            user_id=user.id,
            rfid_code=fake.unique.uuid4(),
            status=choice(['active', 'blocked']),
            created_at=int(fake.date_time_between(start_date='-1y', end_date='now').timestamp()),
        )
        card.set_pin(str(randint(1000, 9999)))
        db.session.add(card)
    db.session.commit()

def generate_logs(users, num_logs=500):
    for _ in range(num_logs):
        user = choice(users)
        log = Log(
            user_id=user.id,
            action_type=choice(['login', 'logout', 'transaction']),
            description=fake.sentence(),
            status=choice(['success', 'failed']),
            timestamp=int(fake.date_time_between(start_date='-1y', end_date='now').timestamp()),
        )
        db.session.add(log)
    db.session.commit()

def populate_database():
    USERS = 50
    TRANSACTIONS = 1000

    print("Generating users...")
    users = generate_users(USERS)
    print(f"Generated {USERS} users. Check 'users_and_passwords.txt' for login details.")

    print("Generating balances...")
    generate_balances(users)
    print("Generated balances.")

    print("Generating transactions...")
    generate_transactions(users, TRANSACTIONS)
    print(f"Generated {TRANSACTIONS} transactions.")

''' Dont need right now
    print("Generating cards...")
    generate_cards(users, 200)
    print("Generated 200 cards.")

    print("Generating logs...")
    generate_logs(users, 500)
    print("Generated 500 logs.")
'''

if __name__ == "__main__":
    app = create_app(config_object='config.DevelopmentConfig')
    with app.app_context():
        populate_database()
