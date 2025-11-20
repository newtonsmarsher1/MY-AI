import os
import sys

from vercel_wsgi import handle

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app import app as flask_app  # noqa: E402


def handler(event, context):
    return handle(flask_app, event, context)


