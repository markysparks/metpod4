import json
import re
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from rainfall import RAINFALL

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


class RAINFALLservice:
    def __init__(self):
        self.recorder = RAINFALL()

    def get_data(self):
        """
        Request the latest sensor data.
        :return: The latest, decoded sensor data.
        """
        return self.recorder.get_total()

    def set_data(self, data):
        """
        Pass the received data to the sensor data decoder.
        :param data: string or JSON formatted 'as read' sensor data.
        """
        tip_amount = self.find_numeric_data(data)
        self.recorder.data_update(tip_amount[0])

    @staticmethod
    def find_numeric_data(dataline):
        """Use regular expressions to find and extract all digit data groups.
        This will include values like 1, 12.3, 2345, 0.34 i.e. any number or
        decimal number.
        :param dataline: The data line from digit groups are to be extracted.
        :return: A list containing the digit groups extracted.
        """
        data_search_exp = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ' \
                          ') )(?:' \
                          '[Ee] [+-]? \d+ ) ?'

        find_data_exp = re.compile(data_search_exp, re.VERBOSE)
        data = find_data_exp.findall(dataline)
        return data


class RAINFALLhttp(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        totals = RAINFALLservice.get_data()
        self.wfile.write(json.dumps(totals[0]['fields']).encode('UTF-8'))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        RAINFALLservice.set_data(str(body))
        self.send_response(200)
        self.end_headers()


""" Start the server that answers requests for readings and inputs received data
for extraction and processing """
RAINFALLservice = RAINFALLservice()

while True:
    server_address = ('', 80)
    httpd = HTTPServer(server_address, RAINFALLhttp)
    logging.info('RAINFALL service running')
    httpd.serve_forever()
