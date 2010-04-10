import os
import sys

localDir = '/home/sean/sites/owgs.org/owgs'
sys.path.append(localDir)

# django land
from django.core.management import setup_environ
from go import settings

setup_environ(settings)


os.environ['DJANGO_SETTINGS_MODULE'] = 'go.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
