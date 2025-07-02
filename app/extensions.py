from flask import Flask
from flask_caching import Cache
from celery import Celery, Task


def celery_init_app(app: Flask) -> Celery:
    '''Initialize Celery with Flask application context.'''
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object("config.CeleryConfig")
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

