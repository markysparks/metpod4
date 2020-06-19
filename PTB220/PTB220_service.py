import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from PTB220_ascii import PTB220_ascii

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


class PTB220service:
    def __init__(self):
        if os.getenv('PTB220_MODE', 'ascii') == 'ascii':
            self.sensor = PTB220_ascii()

    def get_data(self):
        """
        Request the latest sensor data.
        :return: The latest, decoded sensor data.
        """
        return self.sensor.get_readings()


class PTB220http(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        measurements = PTB220service.get_data()
        self.wfile.write(json.dumps(measurements[0]['fields']).encode('UTF-8'))


""" Start the server that answers requests for readings and inputs received data
for extraction and processing """
if os.getenv('PTB220_ENABLE', 'false') == 'true':
    PTB220service = PTB220service()

    while True:
        server_address = ('', 80)
        httpd = HTTPServer(server_address, PTB220http)
        logging.info('PTB220 sensor HTTP server running')
        httpd.serve_forever()
