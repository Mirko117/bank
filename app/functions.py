from flask import current_app, session
import json
import os


def load_language(lang:str):
    '''Load language file'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_translations():
    '''Get translations'''
    lang = session.get('lang', 'en') # Default to English
    return load_language(lang)


def check_language(lang:str):
    '''Check if language file exists'''
    filepath = os.path.join(current_app.root_path, 'languages', f'{lang}.json')
    return os.path.exists(filepath)