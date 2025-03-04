from flask import Blueprint, jsonify, request, render_template, make_response, send_file
from flask_restx import Api, Resource, Namespace
from flask_login import current_user
from io import BytesIO
from decimal import Decimal, ROUND_DOWN
import pandas as pd
import json
from app.functions import get_user_translations, is_valid_number_format, unix_to_datetime, format_money
from app.models import db, Transaction, User, Balance
from app.api.queries import *

# Create blueprint, API and namespace for API
api_bp = Blueprint('api', __name__)
api = Api(api_bp, title="Main API", version="1.0", description="Endpoints for main API")
api_ns = Namespace("api", description="Main operations")

# Create namespace for dashboard
dashboard_ns = Namespace("dashboard", description="Dashboard operations")

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
        
        amount = float(amount.replace(",", "."))

        if amount <= 0:
            response = make_response({"status": "error", "message": "Invalid amount"}, 400)
            return response

        if current_user.get_balance(current_user.settings.default_currency) < amount:
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
                currency = current_user.settings.default_currency,
                status="success",
                transaction_type="transfer",
                description=f"From {current_user.username} to {receiver.username}"
            )

            # Update balances
            current_user.remove_balance(amount, current_user.settings.default_currency)
            receiver.add_balance(amount, current_user.settings.default_currency)

            db.session.add(transaction)
            db.session.commit()

            response = make_response({"status": "success", "message": "Transfer successful"}, 200)

        except Exception as e:
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
                transactions_data = ""
                for transaction in transactions:
                    transactions_data += f"<transaction><date>{unix_to_datetime(transaction.timestamp)}</date><name>{transaction.name}</name><description>{transaction.description}</description><amount>{transaction.amount}</amount><currency>{transaction.currency}</currency></transaction>"
                
                xml_content = f"<transactions>{transactions_data}</transactions>"
                
                output = BytesIO()
                output.write(xml_content.encode("utf-8"))
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

            result = (result * Decimal("0.99")).quantize(Decimal("0.00"), rounding=ROUND_DOWN)  # 1% fee

            # Create transaction
            transaction1 = Transaction(
                name="Currency exchange",
                user_id=current_user.id,
                amount=amount,
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
            response = make_response({"status": "error", "message": "An error occurred"}, 500)
            return response

# Add namespaces to API
api.add_namespace(api_ns, path='/')
api.add_namespace(dashboard_ns, path='/dashboard')
