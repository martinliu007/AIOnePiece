"""
WSGI config for AIOnePiece project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_wsgi_application()

env = os.environ.get('ENV')  # ENV环境变量
if env == "prod":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")
elif env == "stage":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.stage")
elif env == "dev":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")