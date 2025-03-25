from flask import Blueprint, render_template, session, jsonify, request, make_response
from app.functions import get_translations, check_language, is_valid_number_format, format_money
from app.api.queries import get_all_currencies, get_exchange_rate
from decimal import Decimal, ROUND_DOWN

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', t=get_translations(), 
                           all_currencies=get_all_currencies())

@main_bp.route('/set_language/<lang>', methods=['POST'])
def set_language(lang):
    try:
        lang = lang.lower()
        if not check_language(lang):
            return jsonify({"status": "Language not found"}), 404
        session['lang'] = lang
        return jsonify({"status": "Language changed to " + lang}), 200
    except:
        return jsonify({"status": "Error changing language"}), 500


@main_bp.route('/exchange-currencies', methods=['GET'])
def exchange_currencies():
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