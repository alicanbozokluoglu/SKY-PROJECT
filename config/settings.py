from pathlib import Path
# this helps us work with file paths (folders and files)


# this sets the main folder of the project
# Django uses this to find files like templates and database
BASE_DIR = Path(__file__).resolve().parent.parent


# this is a secret key used for security (like encryption)
# it should NOT be shared in real projects
SECRET_KEY = 'django-insecure-*9+^=uhkdg*lxm92k(6q@)zlr*_v9pet-6n$_ro00p_&2n(3)d'


# DEBUG = True means:
# show detailed error messages (good for development)
# should be False in real production
DEBUG = True


# this controls which websites can access this project
# empty means only local use (safe for now)
ALLOWED_HOSTS = []


# this section lists all apps used in the project
# Django built-in apps + your custom app "dashboard"
INSTALLED_APPS = [
    'django.contrib.admin',        # admin panel
    'django.contrib.auth',         # login, users, passwords
    'django.contrib.contenttypes', # handles data types
    'django.contrib.sessions',     # remembers logged-in users
    'django.contrib.messages',     # shows messages like errors/success
    'django.contrib.staticfiles',  # handles static files (CSS, images)
    'dashboard',                  # your custom app
]


# this controls how requests are processed step-by-step
# each middleware adds functionality (security, sessions, etc.)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',         # basic security
    'django.contrib.sessions.middleware.SessionMiddleware', # user sessions
    'django.middleware.common.CommonMiddleware',            # common fixes
    'django.middleware.csrf.CsrfViewMiddleware',            # protects forms
    'django.contrib.auth.middleware.AuthenticationMiddleware', # handles login
    'django.contrib.messages.middleware.MessageMiddleware', # messages system
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # security
]


# this tells Django where URL routes are defined
# it points to "config/urls.py"
ROOT_URLCONF = 'config.urls'


# this controls how templates (HTML files) work
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # this tells Django to look for templates in "templates" folder
        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,  # also look inside each app's templates folder

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  # gives access to request
                'django.contrib.auth.context_processors.auth', # gives access to user
                'django.contrib.messages.context_processors.messages', # messages
            ],
        },
    },
]


# this is for running the server (not very important now)
WSGI_APPLICATION = 'config.wsgi.application'


# this is the database setup
# using SQLite (simple file-based database)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# this controls password rules (security)
# ensures passwords are strong
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # prevents password similar to username
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # enforces minimum length
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # blocks common passwords like "123456"
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # prevents only numbers
    },
]


# language settings
LANGUAGE_CODE = 'en-us'

# time zone (used for database timestamps)
TIME_ZONE = 'UTC'

USE_I18N = True  # allows translations
USE_TZ = True    # uses timezone-aware dates


# this is for static files like images, CSS, JS
STATIC_URL = '/static/'

# this tells Django where to find your static files
STATICFILES_DIRS = [BASE_DIR / "static"]


# ---------------- EMAIL SETTINGS ----------------
# this is VERY important for sending real emails

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# this tells Django to send real emails using SMTP

EMAIL_HOST = 'smtp.gmail.com'
# this is Gmail’s email server

EMAIL_PORT = 587
# this is the standard port for secure email sending

EMAIL_USE_TLS = True
# this encrypts the email connection (secure)

EMAIL_HOST_USER = 'alicanbozokluoglu837@gmail.com'
# this is the email that sends messages

EMAIL_HOST_PASSWORD = 'hnmckhomjpyxtvth'
# this is the app password (NOT your real Gmail password)

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# this sets the "from" email address

"""This file controls the whole project settings.

It tells Django:

where files are
how login works
how database works
how emails are sent"""