import logging
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class RAINFALL:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        self.daily_total = 0.0
        self.scheduler = BackgroundScheduler()

        # Setup scheduled reset of daily rain amount, uses the system time
        self.scheduler.add_job(self.reset_total, CronTrigger(hour=9, minute=0))
        self.scheduler.start()

    def reset_total(self):
        logging.log('Resetting daily rain total to zero')
        self.daily_total = 0.0

    def data_update(self, tip_amount):
        self.daily_total = self.daily_total + float(tip_amount)

    def get_total(self):
        """
        Get the latest instrument readings.
        :return: JSON formatted instrument readings.
        """
        return [
            {
                'measurement': 'rainfall',
                'fields': {
                    'daily_total_mm': round(self.daily_total, 1)
                }
            }
        ]