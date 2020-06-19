import os
import time
import re
import requests
import utils
import warnings
import logging
from datetime import datetime
from apscheduler.triggers.interval import IntervalTrigger
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler


class WOWservice:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        self.metoffice_wow_enable = os.getenv('METOFFICE_WOW_ENABLE', 'true')
        self.wow_tx_interval = int(os.getenv('WOW_TX_INTERVAL', '300'))
        self.wow_site_id = os.getenv('WOW_SITE_ID')
        self.wow_auth_key = os.getenv('WOW_AUTH_KEY')
        self.wow_url = os.getenv('WOW_URL', 'http://wow.metoffice.gov.uk/automaticreading')
        self.softwaretype = os.getenv('SOFTWARETYPE', 'metpod4')
        self.pressure_url = os.getenv('PRESSURE_URL')
        self.humidity_url = os.getenv('HUMIDITY_URL')
        self.temperature_url = os.getenv('TEMPERATURE_URL')
        self.dewpt_url = os.getenv('DEWPT_URL')
        self.winddir_url = os.getenv('WINDDIR_URL')
        self.windspeed_url = os.getenv('WINDSPEED_URL')
        self.raingauge_url = os.getenv('RAINGAUGE_URL')
        self.rainfall_url = os.getenv('RAINFALL_URL')
        self.baro_ht = os.getenv('BARO_HT')
        self.site_altitude = os.getenv('SITE_ALTITUDE')
        self.site_ID = os.getenv('SITE_ID')

        logging.info('MetOffice WOW transmit: ' + self.metoffice_wow_enable)

        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone=utc)

        self.scheduler.add_job(self.transmit_wow_data,
                               IntervalTrigger(seconds=self.wow_tx_interval))

    def transmit_wow_data(self):
        """Transmit a formatted data message to the Met Office WoW website"""
        data = dict()
        pressure = requests.get(self.pressure_url).json()['pressure']
        tempc = requests.get(self.temperature_url).json()['temperature']
        data['humidity'] = requests.get(self.humidity_url).json()['humidity']
        data['tempf'] = utils.to_fahrenheit(tempc)
        data['dewptf'] = utils.to_fahrenheit(requests.get(self.dewpt_url).json()['dew_point'])
        data['rainin'] = utils.to_inches(requests.get(self.raingauge_url).json()['rainrate'])
        data['windgustmph'] = utils.to_mph(requests.get(self.windspeed_url).json()['windgust'])
        data['winddir'] = requests.get(self.winddir_url).json()['winddir_avg10m']
        data['windspeedmph'] = utils.to_mph(requests.get(self.windspeed_url).json()['windspeed_avg10m'])
        data['dailyrainin'] = utils.to_inches(requests.get(self.rainfall_url).json()['daily_total_mm'])
        data['baromin'] = utils.to_inch_hg(utils.calc_qnh_alt(pressure, tempc,
                                                              self.site_altitude, self.baro_ht))

        wow_dtg = datetime.utcnow().strftime("%Y-%m-%d+%H:%M:%S")
        wow_dtg = re.sub(':', '%3A', wow_dtg)
        data['dateutc'] = wow_dtg
        data['softwaretype'] = self.softwaretype
        data['siteid'] = self.wow_site_id
        data['siteAuthenticationKey'] = self.wow_auth_key
        logging.info('WOW-MSG prepped:')
        logging.info(data)

        if self.metoffice_wow_enable == 'true':
            try:
                requests.get(self.wow_url, params=data, timeout=20)
                logging.info('WOW-message transmitted')
            except requests.exceptions.RequestException as e:
                warnings.warn(e, Warning)


WOWservice = WOWservice()

while True:
    if not WOWservice.scheduler.running:
        WOWservice.scheduler.start()
        logging.info('MET OFFICE WOW service running')
    time.sleep(60)
