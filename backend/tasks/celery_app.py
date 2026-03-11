from celery import Celery
from celery.schedules import crontab

from config import DevConfig
from tasks.jobs import daily_deadline_reminders, monthly_admin_report


celery = Celery("placement_portal", broker=DevConfig.CELERY_BROKER_URL, backend=DevConfig.CELERY_RESULT_BACKEND)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=9, minute=0), run_daily_reminders.s())
    sender.add_periodic_task(crontab(day_of_month=1, hour=10, minute=0), run_monthly_report.s())


@celery.task(name="tasks.run_daily_reminders")
def run_daily_reminders():
    return daily_deadline_reminders()


@celery.task(name="tasks.run_monthly_report")
def run_monthly_report():
    return monthly_admin_report()
