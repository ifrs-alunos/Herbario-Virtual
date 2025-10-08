SECRET_KEY = "eg%2hr5a4y@6w+*kipd5by()+vwqkaqqf_s4gj9h%!g_a(l!t6"
HOSTNAME = "localhost"
DEBUG = True
ALLOWED_HOSTS = ["*"]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'labfito',
        'USER': 'postgres',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '5433'
        }
}