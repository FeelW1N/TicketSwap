from celery import Celery


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.task_always_eager = app.config.get("CELERY_TASK_ALWAYS_EAGER", False)
    celery.conf.task_eager_propagates = app.config.get(
        "CELERY_TASK_EAGER_PROPAGATES", False
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
