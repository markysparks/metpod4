import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from RAINGAUGE_ascii import RAINGAUGE_ascii

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


class RAINGAUGEservice:
    def __init__(self):
        if os.getenv('RAINGAUGE_MODE', 'ascii') == 'ascii':
            self.sensor = RAINGAUGE_ascii()

    def get_data(self):
        """
        Request the latest sensor data.
        :return: The latest, decoded sensor data.
        """
        return self.sensor.get_readings()


class RAINGAUGEhttp(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        measurements = RAINGAUGEservice.get_data()
        self.wfile.write(json.dumps(measurements[0]['fields']).encode('UTF-8'))


""" Start the server that answers requests for readings and inputs received data
for extraction and processing """
if os.getenv('RAINGAUGE_ENABLE', 'false') == 'true':
    RAINGAUGEservice = RAINGAUGEservice()

    while True:
        server_address = ('', 80)
        httpd = HTTPServer(server_address, RAINGAUGEhttp)
        logging.info('RAINGAUGE sensor HTTP server running')
        httpd.serve_forever()

