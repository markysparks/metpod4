import os
import json
import time
import requests
import utils
import warnings
import logging
from datetime import datetime
from aws_iot import MQTTclient
from apscheduler.triggers.interval import IntervalTrigger
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler


class AWSIOTservice:
    def __init__(self):

        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        self.aws_iot_enable = os.getenv('AWS_IOT_ENABLE', 'false')
        self.aws_tx_interval = int(os.getenv('AWS_TX_INTERVAL', '300'))
        self.topic = os.getenv('TOPIC', 'mpduk_dev')
        self.aws_mqtt_client = MQTTclient()
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

        logging.info('AWS IoT transmit: ' + self.aws_iot_enable)

        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone=utc)

        self.scheduler.add_job(self.publish_aws_iot,
                               IntervalTrigger(seconds=self.aws_tx_interval))

    def publish_aws_iot(self):
        """Publish observation data to AWS IoT using the MQTT protocol
        provided by mqtt_client.py"""

        data = dict()
        data['pressure'] = requests.get(self.pressure_url).json()['pressure']
        data['trend'] = requests.get(self.pressure_url).json()['pressure_trend']
        data['tendency'] = requests.get(self.pressure_url).json()['pressure_change']
        data['humidity'] = requests.get(self.humidity_url).json()['humidity']
        data['tempc'] = requests.get(self.temperature_url).json()['temperature']
        data['dewptc'] = requests.get(self.dewpt_url).json()['dew_point']
        data['rainrate'] = requests.get(self.raingauge_url).json()['rainrate']
        data['windspeed'] = requests.get(self.windspeed_url).json()['windspeed']
        data['winddir'] = requests.get(self.windspeed_url).json()['winddir']
        data['windgustkts'] = requests.get(self.windspeed_url).json()['windgust']
        data['winddir_avg10m'] = requests.get(self.winddir_url).json()['winddir_avg10m']
        data['windspd_avg10m'] = requests.get(self.windspeed_url).json()['windspeed_avg10m']
        data['dailyrainmm'] = requests.get(self.rainfall_url).json()['daily_total_mm']
        data['day_max'] = None
        data['night_min'] = None
        data['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data['qnh'] = utils.calc_qnh_alt(data['pressure'], data['tempc'],
                                         self.site_altitude, self.baro_ht)
        data['qfe'] = utils.calc_qfe(data['tempc'], data['pressure'], self.baro_ht)
        data['metpodID'] = self.site_ID

        # 'time to live' data expiry parameter used in AWS Dynamo DB table
        data['ttl'] = int(time.time()) + 86400
        data_json = json.dumps(data)
        logging.info('AWS IoT msg prepped:')

        if self.aws_iot_enable == 'true':
            self.aws_mqtt_client.publish(self.topic, data_json)
            logging.info('AWS IoT msg transmitted')
        else:
            logging.info(data_json)


AWSIOTservice = AWSIOTservice()

while True:
    if not AWSIOTservice.scheduler.running:
        AWSIOTservice.scheduler.start()
        logging.info('AWS IoT service running')
    time.sleep(60)
