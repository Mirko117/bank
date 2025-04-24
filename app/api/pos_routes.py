from flask import request, make_response
from flask_restx import Resource, Namespace
from decimal import Decimal
from app.models import db, User, Transaction, PosTerminal, Card


# Create namespace for POS routes
pos_ns = Namespace("pos", description="POS operations")


@pos_ns.route('/make-payment')
class PosLoremEndpoint(Resource):
    def post(self):
        data = request.json

        if not data:
            response = make_response({"message": "No data provided"}, 400)
            return response

        pos_uuid = data.get('pos_uuid')
        rfid = data.get('rfid')
        pin = data.get('pin') if data.get('pin') else None # Optional
        amount = data.get('amount')
        currency = data.get('currency')

        if not all([pos_uuid, rfid, amount, currency]):
            response = make_response({"message": "Missing required fields"}, 400)
            return response

        pos_terminal = PosTerminal.query.filter_by(pos_uuid=pos_uuid).first()

        if not pos_terminal:
            response = make_response({"message": "POS terminal not found"}, 404)
            return response
        
        if not pos_terminal.is_active:
            response = make_response({"message": "POS terminal is inactive"}, 403)
            return response
        
        card = Card.query.filter_by(rfid=rfid).first()

        if not card:
            response = make_response({"message": "Card not found"}, 404)
            return response
        
        if not card.is_active:
            response = make_response({"message": "Card is inactive"}, 403)
            return response
        
        if amount <= 0:
            response = make_response({"message": "Invalid amount"}, 400)
            return response

        user = User.query.filter_by(id=card.user_id).first()

        if not user:
            response = make_response({"message": "User not found"}, 404)
            return response
        
        if user.get_balance(currency) < amount:
            response = make_response({"message": "Insufficient funds"}, 403)
            return response
        
        # For pin
        if amount > Decimal("50.00"):
            if not pin:
                response = make_response({"message": "PIN required"}, 403)
                return response
            
            if not user.verify_pin(pin):
                response = make_response({"message": "Invalid PIN"}, 403)
                return response
        
        owner = User.query.filter_by(id=pos_terminal.owner_id).first()

        if not owner:
            response = make_response({"message": "Owner not found"}, 404)
            return response
        
        try:
            transaction = Transaction(
                name=pos_terminal.name,
                user_id=user.id,
                receiver_id=owner.id,
                amount=amount,
                currency=currency,
                status="success",
                transaction_type="pos_payment",
                pos_terminal_id=pos_terminal.id
            )

            user.remove_balance(amount, currency)
            owner.add_balance(amount, currency)

            db.session.add(transaction)
            db.session.commit()

            response = make_response({"message": "Transaction uccessful"}, 200)
            return response

        except Exception as e:
            db.session.rollback()
            response = make_response({"message": "Transaction failed"}, 500)
            return response