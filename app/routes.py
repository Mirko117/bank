from flask import Blueprint, render_template, session, jsonify
from app.functions import get_translations, check_language

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', t=get_translations())

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
