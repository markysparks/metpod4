import os
import time
import requests
import utils
import warnings
import logging
from apscheduler.triggers.interval import IntervalTrigger
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler


class CORLYSIS_service:
    def __init__(self):

        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        self.colysis_enable = os.getenv('CORLYSIS_ENABLE', 'true')
        self.corlysis_tx_interval = int(os.getenv('CORLYSIS_TX_INTERVAL', '240'))
        self.db = os.getenv('CORLYSIS_DB', 'metpod')
        self.auth = os.getenv('CORLYSIS_AUTH', 'token')
        self.token = os.getenv('TOKEN')
        self.corlysis_url = os.getenv('CORLYSIS_URL', 'https://corlysis.com:8086/write')
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

        logging.info('CORLYSIS transmit: ' + self.colysis_enable)

        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone=utc)

        self.scheduler.add_job(self.transmit_corlysis,
                               IntervalTrigger(seconds=self.corlysis_tx_interval))

    def transmit_corlysis(self):
        """Transmit a formatted data message to Corlysis service"""

        params = {"db": self.db, "u": self.auth, "p": self.token}

        data = dict()
        data['pressure'] = requests.get(self.pressure_url).json()['pressure']
        data['tendency'] = requests.get(self.pressure_url).json()['pressure_change']
        data['humidity'] = requests.get(self.humidity_url).json()['humidity']
        data['tempc'] = requests.get(self.temperature_url).json()['temperature']
        data['dewptc'] = requests.get(self.dewpt_url).json()['dew_point']
        data['rainrate'] = requests.get(self.raingauge_url).json()['rainrate']
        data['windgustkts'] = requests.get(self.windspeed_url).json()['windgust']
        data['winddir_avg10m'] = requests.get(self.winddir_url).json()['winddir_avg10m']
        data['windspd_avg10m'] = requests.get(self.windspeed_url).json()['windspeed_avg10m']
        data['dailyrainmm'] = requests.get(self.rainfall_url).json()['daily_total_mm']
        data['day_max'] = None
        data['night_min'] = None
        data['qnh'] = utils.calc_qnh_alt(data['pressure'], data['tempc'],
                                         self.site_altitude, self.baro_ht)
        data['qfe'] = utils.calc_qfe(data['tempc'], data['pressure'], self.baro_ht)
        data['metpodID'] = self.site_ID

        payload = data['metpodID'] + " temperature={},QNH={},QFE={},pressure={}," \
                                     "tendency={},humidity={},dewpoint={},rainrate={}," \
                                     "dailyrain={} " \
                                     "\n".format(data['tempc'],
                                                 data['qnh'],
                                                 data['qfe'],
                                                 data['pressure'],
                                                 data['tendency'],
                                                 data['humidity'],
                                                 data['dewptc'],
                                                 data['rainrate'],
                                                 data['dailyrainmm']
                                                 )

        payload_wind = data['metpodID'] + " windgust={},winddir={},windspd={} " \
                                          "\n".format(data['windgustkts'],
                                                      data['winddir_avg10m'],
                                                      data['windspd_avg10m']
                                                      )

        logging.info('CORLYSIS MSG prepped:')
        logging.info(payload)
        logging.info(payload_wind)

        if self.colysis_enable == 'true':
            try:
                requests.post(self.corlysis_url, params=params, data=payload, timeout=20)

                if data['winddir_avg10m'] is not None:
                    requests.post(self.corlysis_url, params=params, data=payload_wind, timeout=20)
                    logging.info('CORLYSIS message transmitted')

                # if data['day_max'] is not None and data['night_min'] is not None:
                #     requests.post(url, params=params, data=payload_maxmins, timeout=20)

            except requests.exceptions.RequestException as e:
                warnings.warn(e, Warning)


CORLYSIS_service = CORLYSIS_service()

while True:
    if not CORLYSIS_service.scheduler.running:
        CORLYSIS_service.scheduler.start()
        logging.info('CORLYSIS service running')
    time.sleep(60)
