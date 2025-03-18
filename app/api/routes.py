from flask import Blueprint, jsonify, request, render_template, make_response, send_file
from flask_restx import Api, Resource, Namespace
from flask_login import current_user
from io import BytesIO
from decimal import Decimal, ROUND_DOWN
import validators
import pandas as pd
import json
import os
import xml.etree.ElementTree as ET
from app.functions import get_user_translations, is_valid_number_format, unix_to_datetime, format_money, check_language
from app.models import db, Transaction, User, Balance
from app.api.queries import *
from dotenv import load_dotenv

load_dotenv()

# Create blueprint, API and namespace for API
api_bp = Blueprint('api', __name__)
if os.getenv("FLASK_ENV") == "production":
    api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API", doc=False)
else:
    api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")

# Create namespace for dashboard
dashboard_ns = Namespace("dashboard", description="Dashboard operations")
admin_dashboard_ns = Namespace("admin-dashboard", description="Admin dashboard operations")

### TODO: Add translations to API responses ###

@dashboard_ns.route('/get-shell')
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
            valid_shells = ["dashboard", "transactions", "currencies", "transfers", "settings"]

            if shell not in valid_shells:
                response = make_response({"status": "error", "message": "Shell not found"}, 404)
                return response
            
            # Render the shell
            if shell == "dashboard":
                monthly_income, monthly_change = calculate_monthly_income_and_change()
                recent_transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).limit(4).all()
                total_balance_change = calculate_total_balance_change()
                rendered_shell = render_template("dashboard/shells/dashboard.html", t=get_user_translations(),
                                                 user=current_user, recent_transactions=recent_transactions, 
                                                 monthly_income=monthly_income, monthly_change=monthly_change,
                                                 total_balance_change=total_balance_change)
            elif shell == "transactions":
                transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).all()
                rendered_shell = render_template("dashboard/shells/transactions.html", t=get_user_translations(),
                                                 user=current_user, transactions=transactions)
            elif shell == "currencies":
                rendered_shell = render_template("dashboard/shells/currencies.html", t=get_user_translations(),
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


@dashboard_ns.route('/quick-transfer')
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
            response = make_response({"status": "error", "message": "Invalid amount format. Use 0000.00 or 0000,00"}, 400)
            return response
        
        amount = Decimal(amount.replace(",", "."))

        if amount <= 0:
            response = make_response({"status": "error", "message": "Invalid amount"}, 400)
            return response

        if current_user.get_balance(current_user.settings.default_currency) < amount:
            response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
            return response
        
        # Convert amount to EUR
        exchange_rate = get_exchange_rate(current_user.settings.default_currency, "EUR")
        amount_eur = amount * exchange_rate

        if amount_eur > 1000:
            response = make_response({"status": "error", "message": "Amount must be less than 1000 EUR"}, 400)
            return response
        
        try:
            # Create transaction
            transaction = Transaction(
                name="Quick transfer",
                user_id=current_user.id,
                receiver_id=recipient_query.id,
                amount=amount,
                currency = current_user.settings.default_currency,
                status="success",
                transaction_type="transfer",
                description=f"From {current_user.username} to {recipient_query.username}"
            )

            # Update balances
            current_user.remove_balance(amount, current_user.settings.default_currency)
            recipient_query.add_balance(amount, current_user.settings.default_currency)

            db.session.add(transaction)
            db.session.commit()

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
        
        return response


@dashboard_ns.route('/export-transactions-dialog')
class DashboardExportTransactionsDialogEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            html = render_template("api/export_transactions_dialog.html", t=get_user_translations())

            response = make_response({"status": "success", "html": html, "title": get_user_translations()["transactions"]["export-transactions"]}, 200)
            return response

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/export-transactions')
class DashboardExportTransactionsEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            file_type = request.args.get('file_type')

            if not file_type:
                response = make_response({"status": "error", "message": "File type required"}, 400)
                return response
            
            if file_type not in ["xml", "json", "excel", "pdf"]:
                response = make_response({"status": "error", "message": "Invalid file type"}, 400)
                return response
            
            transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).all()
            
            if file_type == "xml":
                root = ET.Element("transactions")
                for transaction in transactions:
                    trans = ET.SubElement(root, "transaction")
                    ET.SubElement(trans, "date").text = unix_to_datetime(transaction.timestamp)
                    ET.SubElement(trans, "name").text = transaction.name
                    ET.SubElement(trans, "description").text = transaction.description
                    ET.SubElement(trans, "amount").text = str(transaction.amount)
                    ET.SubElement(trans, "currency").text = transaction.currency
                    
                xml_content = ET.tostring(root, encoding="utf-8")
                
                output = BytesIO()
                output.write(xml_content)
                output.seek(0)

                return send_file(output, as_attachment=True, download_name="MiBank_transactions.xml", mimetype="application/xml")

            if file_type == "json":
                transactions_data = [{"date": unix_to_datetime(transaction.timestamp), "name": transaction.name, "description": transaction.description, "amount": float(transaction.amount), "currency": transaction.currency} for transaction in transactions]

                output = BytesIO()
                output.write(json.dumps(transactions_data).encode("utf-8"))
                output.seek(0)

                return send_file(output, as_attachment=True, download_name="MiBank_transactions.json", mimetype="application/json")
            
            if file_type == "excel":
                transactions_data = [{"Date": unix_to_datetime(transaction.timestamp), "Name": transaction.name, "Description": transaction.description, "Amount": transaction.amount, "Currency": transaction.currency} for transaction in transactions]

                df = pd.DataFrame(transactions_data)

                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Transactions")

                output.seek(0)

                return send_file(output, as_attachment=True, download_name="MiBank_transactions.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/add-currency-dialog')
class DashboardAddCurrencyDialogEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            html = render_template("api/add_currency_dialog.html", currencies=get_new_currencies())

            response = make_response({"status": "success", "html": html, "title": get_user_translations()["currencies"]["add-currency"]}, 200)
            return response

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/add-currency')
class DashboardAddCurrencyEndpoint(Resource):
    def post(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            currency = request.form.get("currency")

            if not currency:
                response = make_response({"status": "error", "message": "Currency required"}, 400)
                return response

            if currency not in get_new_currencies():
                response = make_response({"status": "error", "message": "Invalid currency"}, 400)
                return response
            
            new_balance = Balance(user_id=current_user.id, symbol=currency, amount=0.0)
            db.session.add(new_balance)
            db.session.commit()

            response = make_response({"status": "success", "message": "Currency added"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/exchange-currencies')
class DashboardExchangeCurrenciesEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            amount = request.args.get("amount")
            from_currency = request.args.get("from")
            to_currency = request.args.get("to")

            if not amount or not from_currency or not to_currency:
                response = make_response({"status": "error", "message": "Amount, from and to currency required"}, 400)
                return response

            if not is_valid_number_format(amount):
                response = make_response({"status": "error", "message": "Invalid amount format. Use 0000.00 or 0000,00"}, 400)
                return response
            
            amount = Decimal(amount.replace(",", "."))

            if amount <= 0:
                response = make_response({"status": "error", "message": "Invalid amount"}, 400)
                return response
            
            if from_currency == to_currency:
                response = make_response({"status": "error", "message": "Cannot exchange the same currency"}, 400)
                return response
            
            all_currencies = get_all_currencies()
            if from_currency not in all_currencies or to_currency not in all_currencies:
                response = make_response({"status": "error", "message": "Invalid currency"}, 400)
                return response
            
            if current_user.get_balance(from_currency) < amount:
                response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
                return response
            
            exchange_rate = get_exchange_rate(from_currency, to_currency)
            result = amount * exchange_rate

            result = (result * Decimal("0.99")).quantize(Decimal("0.00"), rounding=ROUND_DOWN)  # 1% fee

            result = format_money(result)
            exchange_rate = format_money(exchange_rate, decimals=4)

            response = make_response({"status": "success", "exchange_rate": exchange_rate, "result": result}, 200)
            return response

        except Exception as e:
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

    def post(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        try:
            amount = request.form.get("amount")
            from_currency = request.form.get("from")
            to_currency = request.form.get("to")

            if not amount or not from_currency or not to_currency:
                response = make_response({"status": "error", "message": "Amount, from and to currency required"}, 400)
                return response

            if not is_valid_number_format(amount):
                response = make_response({"status": "error", "message": "Invalid amount format. Use 0000.00 or 0000,00"}, 400)
                return response
            
            amount = Decimal(amount.replace(",", "."))

            if amount <= 0:
                response = make_response({"status": "error", "message": "Invalid amount"}, 400)
                return response
            
            if from_currency == to_currency:
                response = make_response({"status": "error", "message": "Cannot exchange the same currency"}, 400)
                return response
            
            all_currencies = get_all_currencies()
            if from_currency not in all_currencies or to_currency not in all_currencies:
                response = make_response({"status": "error", "message": "Invalid currency"}, 400)
                return response
            
            if current_user.get_balance(from_currency) < amount:
                response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
                return response
            
            exchange_rate = get_exchange_rate(from_currency, to_currency)
            result = amount * exchange_rate

            fee = Decimal("0.01") # 1%
            amount_fee = amount * fee

            result = (result * (Decimal("1") - fee)).quantize(Decimal("0.00"), rounding=ROUND_DOWN)  # 1% fee

            # Create transaction
            transaction1 = Transaction(
                name="Currency exchange",
                user_id=current_user.id,
                amount=amount,
                fee=amount_fee,
                currency=from_currency,
                status="success",
                transaction_type="exchange",
                description=f"Exchanged {amount} {from_currency} to {result} {to_currency}"
            )

            transaction2 = Transaction(
                name="Currency exchange",
                receiver_id=current_user.id,
                amount=result,
                currency=to_currency,
                status="success",
                transaction_type="exchange",
                description=f"Exchanged {amount} {from_currency} to {result} {to_currency}"
            )

            # Update balances
            current_user.remove_balance(amount, from_currency)
            current_user.add_balance(result, to_currency)

            db.session.add(transaction1)
            db.session.add(transaction2)
            db.session.commit()

            response = make_response({"status": "success", "message": "Exchange successful"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/get-transfer-fee')
class DashboardGetTransferFeeEndpoint(Resource):
    def get(self):
        if not current_user.is_authenticated:
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

@dashboard_ns.route('/make-transfer')
class DashboardMakeTransferEndpoint(Resource):
    def post(self):
        if not current_user.is_authenticated:
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

        if current_user.get_balance(currency) < amount:
            response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
            return response
        
        # Convert amount to EUR
        exchange_rate = get_exchange_rate(currency, "EUR")
        amount_eur = amount * exchange_rate

        if amount_eur > 1000:
            fee = Decimal("0.005") # 0.5%
        else:
            fee = Decimal("0")

        fee_amount = amount * fee
        total_amount = amount + fee_amount
        
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
                transaction_type="transfer",
                description=description
            )

            # Update balances
            current_user.remove_balance(total_amount, currency)
            recipient_query.add_balance(amount, currency)

            db.session.add(transaction)
            db.session.commit()

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/save-personal-info')
class DashboardSavePersonalInfoEndpoint(Resource):
    def patch(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')

        if not first_name or not last_name or not username or not email:
            response = make_response({"status": "error", "message": "All fields are required"}, 400)
            return response
        
        if len(first_name) < 3 or len(last_name) < 3 or len(username) < 3:
            response = make_response({"status": "error", "message": "Name and username must be at least 3 characters long"}, 400)
            return response
        
        if any(char.isdigit() for char in first_name) or any(char.isdigit() for char in last_name):
            response = make_response({"status": "error", "message": "Name cannot contain numbers"}, 400)
            return response
        
        if not validators.email(email):
            response = make_response({"status": "error", "message": "Invalid email"}, 400)
            return response
        
        if User.query.filter_by(username=username).first() and username != current_user.username:
            response = make_response({"status": "error", "message": "Username already exists"}, 400)
            return response
        
        if User.query.filter_by(email=email).first() and email != current_user.email:
            response = make_response({"status": "error", "message": "Email already exists"}, 400)
            return response
        
        try:
            if first_name != current_user.first_name:
                current_user.first_name = first_name
            if last_name != current_user.last_name:
                current_user.last_name = last_name
            if username != current_user.username:
                current_user.username = username
            if email != current_user.email:
                current_user.email = email

            db.session.commit()
            
            response = make_response({"status": "success", "message": "Personal info updated"}, 200)
            return response
        
        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response


@dashboard_ns.route('/change-password')
class DashboardChangePasswordEndpoint(Resource):
    def patch(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            response = make_response({"status": "error", "message": "All fields are required"}, 400)
            return response
        
        if new_password != confirm_password:
            response = make_response({"status": "error", "message": "Passwords do not match"}, 400)
            return response
        
        if len(new_password) <= 6:
            response = make_response({"status": "error", "message": "Password must be at least 6 characters long"}, 400)
            return response
        
        if not any(char.isdigit() for char in new_password):
            response = make_response({"status": "error", "message": "Password must contain at least one number"}, 400)
            return response
        
        if not current_user.check_password(current_password):
            response = make_response({"status": "error", "message": "Invalid current password"}, 400)
            return response
        
        try:
            current_user.set_password(new_password)

            db.session.commit()

            response = make_response({"status": "success", "message": "Password changed"}, 200)
            return response
        
        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

@dashboard_ns.route('/save-settings')
class DashboardSaveSettingsEndpoint(Resource):
    def patch(self):
        if not current_user.is_authenticated:
            response = make_response({"status": "error", "message": "Unauthorized"}, 401)
            return response
        
        language = request.form.get('language')
        default_currency = request.form.get('default_currency')

        if not language or not default_currency:
            response = make_response({"status": "error", "message": "All fields are required"}, 400)
            return response
        
        if not check_language(language):
            response = make_response({"status": "error", "message": "Invalid language"}, 400)
            return response
        
        if default_currency not in get_user_currencies():
            response = make_response({"status": "error", "message": "Invalid currency"}, 400)
            return response
        
        try:
            if language != current_user.settings.language:
                current_user.settings.language = language
            if default_currency != current_user.settings.default_currency:
                current_user.settings.default_currency = default_currency

            db.session.commit()

            response = make_response({"status": "success", "message": "Settings updated"}, 200)
            return response
        
        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

# ADMIN

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

        if current_user.get_balance(currency) < amount:
            response = make_response({"status": "error", "message": "Insufficient funds"}, 400)
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

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response






# Add namespaces to API
api.add_namespace(api_ns, path='/')
api.add_namespace(dashboard_ns, path='/dashboard')
api.add_namespace(admin_dashboard_ns, path='/admin-dashboard')