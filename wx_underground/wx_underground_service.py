import os
import time
import requests
import utils
import warnings
import logging
from apscheduler.triggers.interval import IntervalTrigger
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


class WX_UNDERGROUND_service:
    def __init__(self):
        self.wx_underground_enable = os.getenv('WX_UNDERGROUND_ENABLE', 'true')
        self.wx_underground_tx_interval = int(os.getenv('WX_UNDERGROUND_TX_INTERVAL', '300'))
        self.wx_underground_id = os.getenv('WX_UNDERGROUND_ID')
        self.wx_underground_password = os.getenv('WX_UNDERGROUND_PASSWORD')
        self.wx_underground_url = os.getenv('WX_UNDERGROUND_URL')
        self.softwaretype = os.getenv('SOFTWARETYPE')
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

        logging.info('WxUnderground transmit: ' + self.wx_underground_enable)

        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone=utc)

        self.scheduler.add_job(self.transmit_wx_underground,
                               IntervalTrigger(seconds=self.wx_underground_tx_interval))

    def transmit_wx_underground(self):
        """Transmit a formatted data message to the Met Office WoW website"""

        data = dict()
        data['softwaretype'] = self.softwaretype
        data['ID'] = self.wx_underground_id
        data['PASSWORD'] = self.wx_underground_password
        data['action'] = 'updateraw'
        data['realtime'] = 1
        data['rtfreq'] = self.wx_underground_tx_interval
        data['dateutc'] = 'now'

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
        print('WX-UNDERGROUND msg prepped:')
        print(data)

        if self.wx_underground_enable == 'true':
            try:
                requests.get(self.wx_underground_url, params=data, timeout=20)
                print('WX-UNDERGROUND msg transmitted')
            except requests.exceptions.RequestException as e:
                warnings.warn(e)


WX_UNDERGROUND_service = WX_UNDERGROUND_service()

while True:
    if not WX_UNDERGROUND_service.scheduler.running:
        WX_UNDERGROUND_service.scheduler.start()
        logging.info('WX UNDERGROUND service running')
    time.sleep(60)
