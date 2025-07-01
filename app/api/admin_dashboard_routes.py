from flask import request, render_template, make_response
from flask_restx import Resource, Namespace
from flask_login import current_user
from decimal import Decimal, ROUND_DOWN
from app.functions import get_user_translations, is_valid_number_format, delete_cache_on_balance_change
from app.models import db, Transaction, User
from app.api.queries import *


# Create namespace for admin dashboard
admin_dashboard_ns = Namespace("admin-dashboard", description="Admin dashboard operations")

### TODO: Add translations to API responses ###

@admin_dashboard_ns.route('/get-shell')
class AdminDashboardGetPageEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated or current_user.role != "admin":
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        shell = request.args.get('shell')
        
        if not shell:
            response = make_response({"status": "error", "message": "No shell provided"}, 400)
            return response

        try:
            valid_shells = ["admin-transfers", "admin-user-transactions", "settings"]

            if shell not in valid_shells:
                response = make_response({"status": "error", "message": "Shell not found"}, 404)
                return response
            
            # Render the shell
            if shell == "admin-transfers":
                rendered_shell = render_template("dashboard/shells/admin-transfers.html", t=get_user_translations(),
                                                user=current_user, all_currencies=get_all_currencies())
            else:
                rendered_shell = render_template(f"dashboard/shells/{shell}.html", t=get_user_translations(),
                                                user=current_user)
        except Exception as e:
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response   

        if not rendered_shell:
            response = make_response({"status": "error", "message": "Shell not found"}, 404)
            return response

        # Return the rendered shell
        response = make_response({"status": "success", "shell": rendered_shell}, 200)
        return response

@admin_dashboard_ns.route('/get-user-transactions-table')
class AdminDashboardGetUserTransactionsTableEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated or current_user.role != "admin":
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        username = request.args.get('username')

        if not username:
            response = make_response({"status": "error", "message": "Usernmae required"}, 400)
            return response
        
        user = User.query.filter_by(username=username).first()

        if user is None:
            response = make_response({"status": "error", "message": "User not found"}, 404)
            return response
        
        try:
            transactions = user.transactions.order_by(Transaction.timestamp.desc()).all()

            table = render_template("api/user_transactions_table.html", t=get_user_translations(),
                                    user=user, transactions=transactions)

            response = make_response({"status": "success", "table": table}, 200)
            return response

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response


@admin_dashboard_ns.route('/get-transfer-fee')
class DashboardGetTransferFeeEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated or current_user.role != "admin":
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            amount = request.args.get("amount")
            currency = request.args.get("currency")

            if not amount:
                response = make_response({"status": "error", "message": "Amount required"}, 400)
                return response

            if not is_valid_number_format(amount):
                response = make_response({"status": "error", "message": "Invalid amount format. Use 0000.00 or 0000,00"}, 400)
                return response
            
            if not currency:
                response = make_response({"status": "error", "message": "Currency required"}, 400)
                return response
            
            if currency not in get_user_currencies():
                response = make_response({"status": "error", "message": "Currency not found"}, 404)
                return response
            
            amount = Decimal(amount.replace(",", "."))

            if amount <= 0:
                response = make_response({"status": "error", "message": "Invalid amount"}, 400)
                return response
            
            # Convert amount to EUR
            exchange_rate = get_exchange_rate(currency, "EUR")
            amount = amount * exchange_rate

            if amount > 1000:
                fee = 0.005 # 0.5%
            else:
                fee = 0

            response = make_response({"status": "success", "fee": fee}, 200)
            return response

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@admin_dashboard_ns.route('/make-transfer')
class DashboardMakeTransferEndpoint(Resource):
    def post(self):
        if not current_user.is_authenticated or current_user.role != "admin":
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        recipient = request.form.get('recipient')
        amount = request.form.get('amount')
        currency = request.form.get('currency')
        description = request.form.get('description')

        if not recipient or not amount or not currency:
            response = make_response({"status": "error", "message": "Recipient, amount and currency required"}, 400)
            return response

        recipient_query = User.query.filter_by(username=recipient).first()

        if recipient_query is None:
            response = make_response({"status": "error", "message": "Recipient not found"}, 404)
            return response
        
        if recipient_query.id == current_user.id:
            response = make_response({"status": "error", "message": "Cannot transfer to yourself"}, 400)
            return response
        
        if currency not in get_user_currencies():
            response = make_response({"status": "error", "message": "Currency not found"}, 404)
            return response
        
        if not is_valid_number_format(amount):
            response = make_response({"status": "error", "message": "Invalid amount format. Use 0000.00 or 0000,00"}, 400)
            return response
        
        amount = Decimal(amount.replace(",", "."))

        if amount <= 0:
            response = make_response({"status": "error", "message": "Invalid amount"}, 400)
            return response
        
        # Convert amount to EUR
        exchange_rate = get_exchange_rate(currency, "EUR")
        amount_eur = amount * exchange_rate

        if amount_eur > 1000:
            fee = Decimal("0.005") # 0.5%
        else:
            fee = Decimal("0")

        fee_amount = amount * fee
        total_amount = amount - fee_amount
        
        if not description:
            description = f"Transfer from {current_user.username} to {recipient_query.username}"

        try:
            # Create transaction
            transaction = Transaction(
                name="Transfer",
                user_id=current_user.id,
                receiver_id=recipient_query.id,
                amount=total_amount,
                fee=fee_amount,
                currency = currency,
                status="success",
                transaction_type="deposit",
                description=description
            )

            # Update balance
            recipient_query.add_balance(total_amount, currency)

            db.session.add(transaction)
            db.session.commit()

            # Delete related cache
            delete_cache_on_balance_change(recipient_query.id)

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

