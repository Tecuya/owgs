import os


# Django settings for go project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Sean McLean', 'sean@longstair.com'),
)

MANAGERS = ADMINS


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'owgs',                      # Or path to database file if using sqlite3.
        'USER': 'owgs',                      # Not used with sqlite3.
        'PASSWORD': '1934594b',                  # Not used with sqlite3.        
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3. [[in postgres, it seems its necessary to actually say "localhost" here..?
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
}

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'go'             # Or path to database file if using sqlite3.
DATABASE_USER = 'go'             # Not used with sqlite3.
DATABASE_PASSWORD = 'jdfb2b112412f'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'twy75zc#2i*%@2_!6f&&$j1*gt_7k+g-*&i8hk^acyljl^q=u!'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'owgs.urls'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))[:(len('owgs/') * -1)]

STATIC_ROOT = SITE_ROOT + 'static_root'

STATIC_URL = '/static/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    
    'django.contrib.admin',

    'django_extensions',
    'south',
    # 'guardian',

    # for orbited static
    'orbited',

    'registration',
    
    'goserver',
)

ACCOUNT_ACTIVATION_DAYS = 2

AUTH_PROFILE_MODULE = 'goserver.UserProfile'

