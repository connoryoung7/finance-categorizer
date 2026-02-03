from celery import Celery

app = Celery("finance_categorizer")
app.config_from_object("config:celery_settings")
app.autodiscover_tasks(["src.tasks"])
