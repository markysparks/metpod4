import base64
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


class MQTTclient:
    def __init__(self, ):
        """Setup the MQTT client, creating certificate files (for AWS IoT)
        and then configuring the connection to the MQTT broker"""
        cert_root_path = '/usr/src/app/'

        aws_endpoint = os.getenv("AWS_ENDPOINT")
        aws_port = os.getenv("AWS_PORT", 8883)
        device_uuid = os.getenv("METPOD_ID")

        # Save credential files
        self.set_cred("AWS_ROOT_CERT", "root-CA.crt")
        self.set_cred("AWS_THING_CERT", "thing.cert.pem")
        self.set_cred("AWS_PRIVATE_CERT", "thing.private.key")

        # Unique ID. If another connection using the same key is opened the
        # previous one is auto closed by AWS IOT
        self.mqtt_client = AWSIoTMQTTClient(device_uuid)

        # Used to configure the host name and port number the underneath
        # AWS IoT MQTT Client tries to connect to.
        self.mqtt_client.configureEndpoint(aws_endpoint, aws_port)

        # Used to configure the rootCA, private key and certificate files.
        # configureCredentials(CAFilePath, KeyPath='', CertificatePath='')
        self.mqtt_client.configureCredentials(
            cert_root_path + "root-CA.crt",
            cert_root_path + "thing.private.key",
            cert_root_path + "thing.cert.pem")

        # AWSIoTMQTTClient connection configuration
        self.mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)

        # Configure the offline queue for publish requests to be 20 in size
        # and drop the oldest
        self.mqtt_client.configureOfflinePublishQueueing(-1)

        # Used to configure the draining speed to clear up the queued requests
        # when the connection is back. (frequencyInHz)
        self.mqtt_client.configureDrainingFrequency(2)

        # Configure connect/disconnect timeout to be 10 seconds
        self.mqtt_client.configureConnectDisconnectTimeout(10)

        # Configure MQTT operation timeout to be 5 seconds
        self.mqtt_client.configureMQTTOperationTimeout(5)

    @staticmethod
    def set_cred(env_name, file_name):
        """Turn base64 encoded environmental variable into a certificate file.
        :param env_name: The environmental variable that contains the base64
        string to be converted into a certificate file.
        :param file_name: The certificate filename to be used."""
        env = os.getenv(env_name)
        with open(file_name, "wb") as output_file:
            output_file.write(base64.b64decode(env))

    def publish(self, topic, message_json):
        """Publish a message using the MQTT client.
        :param topic: The MQTT message topic to be used.
        :param message_json: JSON formatted message."""
        self.mqtt_client.connect()
        self.mqtt_client.publish(topic, message_json, 1)
        print('Published topic %s: %s\n' % (topic, message_json))
        self.mqtt_client.disconnect()

