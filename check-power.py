#
#
# MONITOR MQTT:
# mosquitto_sub -h 192.168.147.1 -t ha/tts/picotts_say
#

import json
from datetime import datetime, timedelta
import logging
import sys
import paho.mqtt.client as mqtt
import numpy as np
import talib
import argparse

logger = logging.getLogger('check-power')
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
TIMEZONE_IOT_OFFSET_HOURS = 1  # evita di cambiare il timezone ad ogni sensore della rete
EXPIRE_SEC = 45
MESSAGE_EMA_LEVEL = 16

# power meter measure
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
TOPIC_PC_POWER = "tele/tasmota_9D1588/SENSOR"
reading_watt_pc_power = 0
expire_pc_power_sec = EXPIRE_SEC
time_watt_pc_power = datetime.now()
TOPIC_BAGNO_POWER = "tele/tasmota_CEAA9C/SENSOR"
reading_watt_bagno_power = 0
expire_bagno_power_sec = EXPIRE_SEC
time_watt_bagno_power = datetime.now()
# totals
total_watt_last = 0
total_watt = 0
total_watt_var = 0  # variazione percentuale dall'ultima lettura
TOTAL_WATT_MAX = 3000  # 3 kilowatt di contratto
# filters
power_watt_series = np.zeros(10)
total_watt_last_ema = 0
# external lux meter
ENABLE_EXTERNAL_LUX_METER = False
TOPIC_EXTERNAL_LUX_METER = "tele/tasmota_A6C75F/SENSOR"
lux_check_points = [0, 1, 2, 5, 7.5, 10, 20, 30, 40, 50, 100, 200, 500, 750, 1000, 2000, 5000, 7500, 10000, 20000, 50000]
lux_check_points_hist_min = [x - (x * 10 / 100.0) for x in lux_check_points]
lux_check_points_hist_max = [x + (x * 10 / 100.0) for x in lux_check_points]
lux_check_points_last = -1


#
# power meter measure
# The callback for when the client receives a CONNACK response from the server.
#
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_GR_FRIGO)  # gr.frigo
    client.subscribe(TOPIC_GR_PIASTRA)  # gr.piastra
    client.subscribe(TOPIC_GR_MICROWAV)  # microwav
    client.subscribe(TOPIC_GR_BOILER)  # boiler
    client.subscribe(TOPIC_PC_POWER)  # power meter, posiz. pC
    client.subscribe(TOPIC_BAGNO_POWER)  # power meter, posiz, prese bagno
    # external lux meter
    if ENABLE_EXTERNAL_LUX_METER:
        client.subscribe(TOPIC_EXTERNAL_LUX_METER)


# The callback for when a PUBLISH message is received from the server.
# ATTENZIONE: l'intera procedura deve durare max 30 secondi
def on_message(client, userdata, msg):
    logger.debug(msg.topic + " " + str(msg.payload))
    global reading_watt_frigo, reading_watt_piastra, reading_watt_microwav, reading_watt_boiler, reading_watt_pc_power
    global reading_watt_bagno_power
    global time_watt_frigo, time_watt_piastra, time_watt_microwav, time_watt_boiler, time_watt_pc_power
    global time_watt_bagno_power
    global total_watt, total_watt_last, total_watt_var, power_watt_series, total_watt_last_ema
    global lux_check_points_last

    now = datetime.now()
    value = json.loads(msg.payload)

    if msg.topic in [TOPIC_GR_FRIGO, TOPIC_GR_PIASTRA, TOPIC_GR_MICROWAV, TOPIC_GR_BOILER,
                     TOPIC_PC_POWER, TOPIC_BAGNO_POWER]:
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
        elif msg.topic == TOPIC_PC_POWER:
            reading_watt_pc_power = watt
            time_watt_pc_power = t
            logger.debug("pc power W {:d} {}".format(reading_watt_pc_power, time_watt_pc_power))
        elif msg.topic == TOPIC_BAGNO_POWER:
            reading_watt_bagno_power = watt
            time_watt_bagno_power = t
            logger.debug("bagno prese power W {:d} {}".format(reading_watt_bagno_power, time_watt_bagno_power))
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
        if (datetime.now() - time_watt_pc_power).total_seconds() > EXPIRE_SEC:
            time_watt_pc_power = datetime.now()
            reading_watt_pc_power = 0
        if (datetime.now() - time_watt_bagno_power).total_seconds() > EXPIRE_SEC:
            time_watt_bagno_power = datetime.now()
            reading_watt_bagno_power = 0
        # calcolo
        total_watt = reading_watt_frigo + reading_watt_piastra + reading_watt_microwav + reading_watt_boiler + \
                     reading_watt_pc_power + reading_watt_bagno_power
        total_watt_var = round(-(total_watt_last - total_watt) / TOTAL_WATT_MAX * 100.0, 1)
        total_watt_perc = round(total_watt / TOTAL_WATT_MAX * 100.0, 1)
        power_watt_series = np.delete(power_watt_series, 0)
        power_watt_series = np.append(power_watt_series, total_watt)
        # EMA = exponential moving average
        # FIR filter
        total_watt_ema = round(talib.EMA(power_watt_series, timeperiod=4)[10 - 1])
        total_watt_var_ema = round(-(total_watt_last_ema - total_watt_ema) / TOTAL_WATT_MAX * 100.0, 1)

        # if total_watt_var > 200:
        logger.info("total W {:d} var % {} load % {} EMA4 W {} var EMA4 % {}"
                    .format(total_watt, total_watt_var, total_watt_perc, total_watt_ema, total_watt_var_ema))
        # update
        total_watt_last = total_watt
        total_watt_last_ema = total_watt_ema

        message = None
        if total_watt_var_ema > MESSAGE_EMA_LEVEL:
            message = "la potenza sta salendo al {} percento".format(round(total_watt_perc))
        if total_watt_var_ema < -MESSAGE_EMA_LEVEL:
            message = "la potenza sta scendendo al {} percento".format(round(total_watt_perc))
        if message is not None:
            # tts @ home assistant
            payload = {"time": now.strftime(TIME_FORMAT),
                       "speech": {"entity_id": args.HA_MEDIA_PLAYER_ID, "language": 'it-IT', "message": message}}
            client.publish(args.HA_TTS_SERVICE_TOPIC, json.dumps(payload))
    if ENABLE_EXTERNAL_LUX_METER and msg.topic in [TOPIC_EXTERNAL_LUX_METER]:
        lux = value["TSL2561"]["Illuminance"]
        logger.info(f"lux meter: {lux} last: {lux_check_points_last}")
        message = None
        for i, v in enumerate(lux_check_points):
            if lux_check_points_hist_min[i] <= lux <= lux_check_points_hist_max[i]:
                if lux_check_points_last != v:
                    lux_check_points_last = v
                    if v == 0:
                        message = f"buio"
                    else:
                        message = f"luce {int(lux)}"
                    logger.info(f"lux meter message: {message}")
        if message is not None:
            # tts @ home assistant
            payload = {"time": now.strftime(TIME_FORMAT),
                       "speech": {"entity_id": args.HA_MEDIA_PLAYER_ID, "language": 'it-IT', "message": message}}
            client.publish(args.HA_TTS_SERVICE_TOPIC, json.dumps(payload))


parser = argparse.ArgumentParser(
    prog='check-power',
    description='get power meters value and filter readings')
parser.add_argument('--HA_MEDIA_PLAYER_ID', default="media_player.mopidy")
parser.add_argument('--HA_TTS_SERVICE_TOPIC', default="ha/tts/picotts_say")
args = parser.parse_args()
print(f"HA_MEDIA_PLAYER_ID: {args.HA_MEDIA_PLAYER_ID}")
print(f"HA_TTS_SERVICE_TOPIC: {args.HA_TTS_SERVICE_TOPIC}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.147.1", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
