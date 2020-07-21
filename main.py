#
#
#

import json
from datetime import datetime, timedelta
import logging
import sys
import paho.mqtt.client as mqtt
import numpy as np
import talib

logger = logging.getLogger('check-power')
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
TIMEZONE_IOT_OFFSET_HOURS = 1  # evita di cambiare il timezone ad ogni sensore della rete
EXPIRE_SEC = 45

# measure
TOPIC_GR_FRIGO = "tele/tasmota_6835DF/SENSOR"
reading_watt_frigo = 0
expire_frigo_sec = EXPIRE_SEC
time_watt_frigo = datetime.now()
TOPIC_GR_PIASTRA = "tele/tasmota_3D5CA8/SENSOR"
reading_watt_piastra = 0
expire_piastra_sec = EXPIRE_SEC
time_watt_piastra = datetime.now()
TOPIC_GR_MICROWAV = "tele/tasmota_67EAC1/SENSOR"
reading_watt_microwav = 0
expire_microwav_sec = EXPIRE_SEC
time_watt_microwav = datetime.now()
TOPIC_GR_BOILER = "tele/tasmota_67E683/SENSOR"
reading_watt_boiler = 0
expire_boiler_sec = EXPIRE_SEC
time_watt_boiler = datetime.now()
# totals
total_watt_last = 0
total_watt = 0
total_watt_var = 0      # variazione percentuale dall'ultima lettura
TOTAL_WATT_MAX = 3000   # 3 kilowatt di contratto
# filters
power_watt_series = np.zeros(10)
total_watt_last_ema = 0


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_GR_FRIGO)  # gr.frigo
    client.subscribe(TOPIC_GR_PIASTRA)  # gr.piastra
    client.subscribe(TOPIC_GR_MICROWAV)  # microwav
    client.subscribe(TOPIC_GR_BOILER)  # boiler


# The callback for when a PUBLISH message is received from the server.
# ATTENZIONE: l'intera procedura deve durare max 30 secondi
def on_message(client, userdata, msg):
    logger.debug(msg.topic+" "+str(msg.payload))
    global reading_watt_frigo, reading_watt_piastra, reading_watt_microwav, reading_watt_boiler
    global time_watt_frigo, time_watt_piastra, time_watt_microwav, time_watt_boiler
    global total_watt, total_watt_last, total_watt_var, power_watt_series, total_watt_last_ema

    value = json.loads(msg.payload)
    watt = value["ENERGY"]["Power"]
    t = datetime.strptime(value["Time"], TIME_FORMAT) + timedelta(hours=TIMEZONE_IOT_OFFSET_HOURS)
    if msg.topic == TOPIC_GR_FRIGO:
        reading_watt_frigo = watt
        time_watt_frigo = t
        logger.debug("frigo  W {:d} {}".format(reading_watt_frigo, time_watt_frigo))
    elif msg.topic == TOPIC_GR_PIASTRA:
        reading_watt_piastra = watt
        time_watt_piastra = t
        logger.debug("piastr W {:d} {}".format(reading_watt_piastra, time_watt_piastra))
    elif msg.topic == TOPIC_GR_MICROWAV:
        reading_watt_microwav = watt
        time_watt_microwav = t
        logger.debug("microw W {:d} {}".format(reading_watt_microwav, time_watt_microwav))
    elif msg.topic == TOPIC_GR_BOILER:
        reading_watt_boiler = watt
        time_watt_boiler = t
        logger.debug("boiler W {:d} {}".format(reading_watt_boiler, time_watt_boiler))
    # scadenza valori
    if (datetime.now() - time_watt_frigo).total_seconds() > EXPIRE_SEC:
        time_watt_frigo = datetime.now()
        reading_watt_frigo = 0
    if (datetime.now() - time_watt_piastra).total_seconds() > EXPIRE_SEC:
        time_watt_piastra = datetime.now()
        reading_watt_piastra = 0
    if (datetime.now() - time_watt_microwav).total_seconds() > EXPIRE_SEC:
        time_watt_microwav = datetime.now()
        reading_watt_microwav = 0
    if (datetime.now() - time_watt_boiler).total_seconds() > EXPIRE_SEC:
        time_watt_boiler = datetime.now()
        reading_watt_boiler = 0
    # calcolo
    total_watt = reading_watt_frigo + reading_watt_piastra + reading_watt_microwav + reading_watt_boiler
    total_watt_var = round(-(total_watt_last - total_watt) / TOTAL_WATT_MAX * 100.0, 1)
    total_watt_perc = round(total_watt / TOTAL_WATT_MAX * 100.0, 1)
    power_watt_series = np.delete(power_watt_series, 0)
    power_watt_series = np.append(power_watt_series, total_watt)
    # EMA = exponential moving average
    # FIR filter
    total_watt_ema = round(talib.EMA(power_watt_series, timeperiod=4)[10-1])
    total_watt_var_ema = round(-(total_watt_last_ema - total_watt_ema) / TOTAL_WATT_MAX * 100.0, 1)

    # if total_watt_var > 200:
    logger.info("total W {:d} var % {} load % {} EMA4 W {} var EMA4 % {}"
                .format(total_watt, total_watt_var, total_watt_perc, total_watt_ema, total_watt_var_ema))
    # update
    total_watt_last = total_watt
    total_watt_last_ema = total_watt_ema


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.147.1", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
