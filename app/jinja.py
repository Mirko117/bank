from jinja2 import Environment
from datetime import datetime

def set_jinja_environment(app):

    # Custom filter function
    def unix_to_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        # Convert timestamp to datetime and format it
        return datetime.fromtimestamp(value).strftime(format)

    # Add custom filter to Flask's Jinja environment
    app.jinja_env.filters['datetime'] = unix_to_datetime