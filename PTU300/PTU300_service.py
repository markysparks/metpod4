import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from PTU300_ascii import PTU300_ascii
# from PTU300_modbus import PTU300_modbus
logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


class PTU300service:
    def __init__(self):
        if os.getenv('PTU300_MODE', 'ascii') == 'ascii':
            self.sensor = PTU300_ascii()
        # elif os.getenv('PTU300_MODE', 'ascii') == 'modbus':
        #     self.sensor = PTU300_modbus

    def get_data(self):
        """
        Request the latest sensor data.
        :return: The latest, decoded sensor data.
        """
        return self.sensor.get_readings()


class PTU300http(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        measurements = PTU300service.get_data()
        self.wfile.write(json.dumps(measurements[0]['fields']).encode('UTF-8'))


""" Start the server that answers requests for readings and inputs received data
for extraction and processing """
if os.getenv('PTU300_ENABLE', 'false') == 'true':
    PTU300service = PTU300service()

    while True:
        server_address = ('', 80)
        httpd = HTTPServer(server_address, PTU300http)
        logging.info('PTU300 sensor HTTP server running')
        httpd.serve_forever()
