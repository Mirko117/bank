from flask import current_app, session
import json
import os


# Load language files
def load_language(lang:str):
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    with open(filepath, 'r') as f:
        return json.load(f)


# Get translations
def get_translations():
    lang = session.get('lang', 'en') # Default to English
    return load_language(lang)


# Check if language file exists
def check_language(lang:str):
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    return os.path.exists(filepath)