release: python manage.py migrate --noinput
web: gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker corporatum.asgi:application
worker: celery -A corporatum worker -P prefork --loglevel=INFO 
beat: celery -A corporatum beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
