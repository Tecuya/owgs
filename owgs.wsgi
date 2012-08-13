import os
import sys

# init django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'owgs.settings' )

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if debug:
    # if debug, install the logging middleware
    application = LoggingMiddleware(application)

