import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG
CACHE_BACKEND = 'file:///home/nexus/django_cache?timeout=900'

ADMINS = (
    ('Nexus Developers', 'dev@wvnexus.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql'
DATABASE_NAME = 'nexus'
DATABASE_USER = 'nexus'
DATABASE_PASSWORD = open('/home/nexus/.DATABASE_PASSWORD').read()
DATABASE_HOST = ''
DATABASE_PORT = ''
TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = '/home/nexus/webapps/site_media/'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'
SECRET_KEY = open('/home/nexus/.SECRET_KEY').read()
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'nexus.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'archive/templates').replace('\\','/'),
    os.path.join(os.path.dirname(__file__), 'cover/templates').replace('\\','/'),
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.webdesign',
    'django.contrib.markup',
    'nexus.cover',
    'nexus.archive',
    'nexus.bugs_and_ideas',
    'django_evolution',
)
