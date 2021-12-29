release: python manage.py migrate --noinput
web: gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker tgbot.asgi:application
worker: celery -A tgbot worker -P prefork --loglevel=INFO 
beat: celery -A dtb beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
