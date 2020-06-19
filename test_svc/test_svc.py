import requests
import time
import os
import logging
# import json
# import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


def print_msg():

    # client = mqtt.Client('testsvc')
    # client.connect('mqtt')

    while True:
        # requests.post('http://PTB220', data='.P.1  1012.05 ***.* * 1012.15 1012.0 1012.0 000.D5')
        # requests.post('http://PTU300', data="P=  1003.8 hPa   T= 17.7 'C RH= 40.9 %RH TD=  4.3 'C  trend=0.2 tend=7")
        # requests.post('http://WINDSONIC', data="\x02Q,194,005.04,N,00,\x0315")
        # requests.post('http://RAINGAUGE', data='{"rainrate": 0.3, "raintip": 0.2, "units": "mm/hr"}')

        if os.getenv('PTB220_TEST', 'false') == 'true':
            PTB220_data = requests.get('http://PTB220', timeout=5).json()
            # client.publish('PTB220/data', payload=str(json.dumps(PTB220_data)))
            logging.info('PTB220: ' + str(PTB220_data))
            logging.info(PTB220_data['pressure'])
            logging.info(PTB220_data['pressure_change'])

        if os.getenv('PTU300_TEST', 'false') == 'true':
            PTU300_data = requests.get('http://PTU300', timeout=5).json()
            logging.info('PTU300: ' + str(PTU300_data))

        if os.getenv('WINDSONIC_TEST', 'false') == 'true':
            windsonic_data = requests.get('http://WINDSONIC', timeout=5).json()
            logging.info('WINDSONIC: ' + str(windsonic_data))

        if os.getenv('RAINGAUGE_TEST', 'false') == 'true':
            raingauge_data = requests.get('http://RAINGAUGE', timeout=5).json()
            logging.info('RAINGAUGE: ' + str(raingauge_data))

        if os.getenv('RAINFALL_TEST', 'false') == 'true':
            rainfall_data = requests.get('http://rainfall', timeout=5).json()
            logging.info('RAINFALL: ' + str(rainfall_data))

        time.sleep(10)


if __name__ == '__main__':
    print_msg()
