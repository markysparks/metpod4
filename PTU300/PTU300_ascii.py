import warnings
import logging
import re
import os
import serial
import value_checks
from datetime import datetime
from threading import Timer


class PTU300_ascii:
    def __init__(self):
        """Vaisala PTU300 sensor data extraction class. Extracts pressure,
        temperature, humidity and dew point from the sensor data output."""
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        # b"P=  1003.8 hPa   T= 17.7 'C RH= 40.9 %RH TD=  4.3 'C  trend=*****
        # tend=*\r\n"
        self.ptu300_pattern = re.compile('P=.+hPa.+T=.+RH=.+TD=.+trend=.+tend=.')

        self.serial_port_name = os.getenv('PTU300_PORT', '/dev/ttyUSB0')
        self.serial_baud = os.getenv('PTU300_BAUD', 9600)
        self.serial_port = serial.Serial(self.serial_port_name, self.serial_baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))
        logging.info('Sensor mode: ascii')

        self.timestamp = None
        self.pressure = None
        self.temperature = None
        self.humidity = None
        self.dew_point = None
        self.pressure_change = None
        self.pressure_trend = None

        self.serial_port_reader()

    def serial_port_reader(self):
        """Read a line of incoming data from the assigned serial port, then
        pass the data onto a processor for extraction of the data values"""
        try:
            data_bytes = self.serial_port.readline()
            data_line = str(data_bytes)
            # Only process output if we have actual data in the line
            if len(data_line) > 3:
                logging.info('RAW data: ' + data_line)
                self.data_decoder(data_line)
                logging.info(self.get_readings())
        except serial.SerialException as error:
            warnings.warn("Serial port error: " + str(error), Warning)
        # Asynchronously schedule this function to be run again in 1.0 seconds
        Timer(1, self.serial_port_reader).start()

    def data_decoder(self, data_line):
        """
        Extract available weather parameters from the sensor data, check that
        data falls within sensible boundaries. if necessary, the sensor must
        be setup to output its data in the required format e.g.
        P=  1003.8 hPa   T= 17.4 'C RH= 41.3 %RH " TD= 4.2 'C  trend=-0.4 tend=7
        with units of hPa, degrees C and % humidity.
        :param data_line: Sensor data output string.
        """
        """ Apply any instrument corrections """
        pressure_correction = float(os.getenv('PRESS_CORR', 0.0))
        temperature_correction = float(os.getenv('TEMP_CORR', 0.0))
        humidity_correction = float(os.getenv('HUMI_CORR', 0.0))

        """ Check we have PTU300 data available and then extract numeric
        values from this data """
        if self.ptu300_pattern.search(data_line):
            data = find_numeric_data(data_line)
            if 3 < len(data) < 7:
                self.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                pressure = float(data[0]) + pressure_correction
                temperature = float(data[1]) + temperature_correction
                humidity = int(round(float(data[2]) +
                                     humidity_correction, 0))
                dew_point = float(data[3])
                pressure_change = None
                pressure_trend = None

                # This sensor can output e.g. 102% humidity which is
                # probably correct (supersaturation) but not accepted by
                # e.g. weather underground map display data.
                if humidity > 100:
                    humidity = 100

                """ Pressure change and trend is only available and 
                output after 3 hours"""
                if len(data) > 4:
                    pressure_change = float(data[4])
                if len(data) > 5:
                    pressure_trend = int(data[5])

                """ Check parameters fall within sensible limits """
                if value_checks.pressure_check(pressure):
                    self.pressure = pressure

                if value_checks.humidity_check(humidity):
                    self.humidity = humidity

                if value_checks.temperature_check(temperature):
                    self.temperature = temperature

                if value_checks.temperature_check(dew_point):
                    self.dew_point = dew_point

                if value_checks.tendency_check(pressure_change):
                    self.pressure_change = pressure_change

                if value_checks.trend_check(pressure_trend):
                    self.pressure_trend = pressure_trend

            else:
                warnings.warn('invalid PTU300 data!', Warning)

    def get_readings(self):
        """
        Return the latest recorded values from the instrument
        :return: JSON formatted instrument readings
        """
        return [
            {
                'measurement': 'PTU300',
                'fields': {
                    'timestamp': self.timestamp,
                    'pressure': self.pressure,
                    'temperature': self.temperature,
                    'dew_point': self.dew_point,
                    'humidity': self.humidity,
                    'pressure_change': self.pressure_change,
                    'pressure_trend': self.pressure_trend
                }
            }
        ]


def find_numeric_data(data_line):
    """Use regular expressions to find and extract all digit data groups.
    This will include values like 1, 12.3, 2345, 0.34 i.e. any number or
    decimal number.
    :param data_line: The data line from digit groups are to be extracted.
    :return: A list containing the digit groups extracted.
    """
    data_search_exp = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ' \
                      ') )(?:' \
                      '[Ee] [+-]? \d+ ) ?'

    find_data_exp = re.compile(data_search_exp, re.VERBOSE)
    data = find_data_exp.findall(data_line)
    return data


if __name__ == '__main__':
    PTU300_ascii()
