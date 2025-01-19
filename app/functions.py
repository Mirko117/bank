from flask import current_app, session
from flask_login import current_user
import json
import os
import re


def load_language(lang:str):
    '''Load language file'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_language(lang:str):
    '''Check if language file exists'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    return os.path.exists(filepath)

def get_translations():
    '''Get translations'''
    lang = session.get('lang', 'en') # Default to English
    return load_language(lang)

def get_user_translations():
    '''Get translations for current user'''
    lang = current_user.settings.language
    if not check_language(lang):
        lang = 'en'
    return load_language(lang)

def is_valid_number_format(s):
    '''Check if a string is a valid number format'''
    # Regular expression to match numbers with only one comma or period
    pattern = r'^\d+(?:[.,]\d{1,2})?$'
    return bool(re.match(pattern, s))