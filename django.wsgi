import os
import sys

sys.path.append('/home/sean/sites/owgs.org/owgs')
os.environ['DJANGO_SETTINGS_MODULE'] = 'go.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
