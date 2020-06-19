# metpod4
Automatic IoT weather station using Raspberry Pi, Balena OS and containers.

Using Balena Cloud and Balena OS on a Raspberry Pi/Balena Fin carrier board, this automatic weather station collects 
and processes weather data from a range of RS232/485 ascii/ModBus sensors (e.g. Vaisala PTB220, PTU300, Gill Windsonic), then sends the 
data to various services e.g. Wx Underground, AWS IoT, Corlysis (InfluxDB/Grafana) and Met Office WOW. 

Each sensor and IoT service is handled by its own container to make a modular and extensible framework.
As part of an IoT fleet of devices, the system can easily be managed and upgraded remotely.

