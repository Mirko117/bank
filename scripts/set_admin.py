import sys
from pathlib import Path

# This runs script from the project root directory
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models import User
from config import Config

# Check if username was provided
if len(sys.argv) < 2:
    print("Error: Please provide a username")
    print("Usage: python set_admin.py <username>")
    sys.exit(1)

# Get username from command line
username = sys.argv[1]

# Create app context
app = create_app(Config)

with app.app_context():
    # Find the user
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        print(f"Error: User '{username}' not found")
        sys.exit(1)
        
    # Check if user is already an admin
    if user.role == 'admin':
        print(f"User '{username}' is already an admin")
        sys.exit(0)
    
    # Update user role
    old_role = user.role
    user.role = 'admin'
    
    try:
        # Save changes to database
        db.session.commit()
        print(f"Success: Changed user '{username}' role from '{old_role}' to 'admin'")
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to update user role: {str(e)}")
        sys.exit(1)



