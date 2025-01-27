from flask import Blueprint, jsonify, request, render_template, make_response
from flask_restx import Api, Resource, Namespace
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.functions import get_user_translations, is_valid_number_format
from app.models import db, Transaction, User
from app.api.queries import calculate_monthly_income_and_change

# Create blueprint, API and namespace for API
api_bp = Blueprint('api', __name__)
api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")

# Create namespace for dashboard
dashbpard_ns = Namespace("dashboard", description="Dashboard operations")

@dashbpard_ns.route('/get-shell')
class DashboardGetPageEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        shell = request.args.get('shell')
        
        if not shell:
            response = make_response({"status": "error", "message": "No shell provided"}, 400)
            return response

        try:
            # Render the shell
            if shell == "dashboard":
                monthly_income = calculate_monthly_income_and_change()
                recent_transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).limit(4).all()
                rendered_shell = render_template("dashboard/shells/dashboard.html", t=get_user_translations(), user=current_user, recent_transactions=recent_transactions, monthly_income=monthly_income)
            elif shell == "transactions":
                transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).all()
                rendered_shell = render_template("dashboard/shells/transactions.html", t=get_user_translations(), user=current_user, transactions=transactions)
            else:
                rendered_shell = render_template(f"dashboard/shells/{shell}.html", t=get_user_translations(), user=current_user)
        except Exception as e:
            print(e)
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response   

        if not rendered_shell:
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response

        # Return the rendered shell
        response = make_response({"status": "success", "shell": rendered_shell}, 200)
        return response


@dashbpard_ns.route('/quick-transfer')
class DashboardMakeQuickTransferEndpoint(Resource):
    def post(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        recipient = request.form.get('recipient')
        amount = request.form.get('amount')

        if not recipient or not amount:
            response = make_response({"status": "error", "message": "Recipient and amount required"}, 400)
            return response

        recipient_query = User.query.filter_by(username=recipient).first()

        if recipient_query is None:
            response = make_response({"status": "error", "message": "Recipient not found"}, 404)
            return response
        
        if recipient_query.id == current_user.id:
            response = make_response({"status": "error", "message": "Cannot transfer to yourself"}, 400)
            return response
        
        if not is_valid_number_format(amount):
            response = make_response({"status": "error", "message": "Invalid amount formar. Use 0000.00 or 0000,00"}, 400)
            return response
        
        amount = float(amount.replace(",", "."))

        if amount <= 0:
            response = make_response({"status": "error", "message": "Invalid amount"}, 400)
            return response

        if current_user.balance < amount:
            response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
            return response
        
        try:
            receiver = User.query.filter_by(username=recipient).first()
            
            # Create transaction
            transaction = Transaction(
                name="Quick transfer",
                user_id=current_user.id,
                receiver_id=receiver.id,
                amount=amount,
                status="success",
                transaction_type="transfer"
            )

            # Update balances
            current_user.balance = round(current_user.balance - amount, 2)
            receiver.balance = round(receiver.balance + amount, 2)

            db.session.add(transaction)
            db.session.commit()

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
        
        return response



# Add namespaces to API
api.add_namespace(api_ns, path='/')
api.add_namespace(dashbpard_ns, path='/dashboard')
