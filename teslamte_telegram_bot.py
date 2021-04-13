#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import os
import time
from datetime import datetime
import json
import requests

import paho.mqtt.client as mqtt

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# initializing the bot with API_KEY and CHAT_ID
if os.getenv('TELEGRAM_BOT_API_KEY') == None:
	print("Error: Please set the environment variable TELEGRAM_BOT_API_KEY and try again.")
	exit(1)

bot = Bot(os.getenv('TELEGRAM_BOT_API_KEY'))
if os.getenv('TELEGRAM_BOT_CHAT_ID') == None:
	print("Error: Please set the environment variable TELEGRAM_BOT_CHAT_ID and try again.")
	exit(1)

chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')

notif_conduite = False
notif_charge = True
notif_porte = True
notif_locked = True

# based on example from https://pypi.org/project/paho-mqtt/
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))
	if rc == 0:
		print("Connected successfully to broker")
		bot.send_message(
			chat_id,
			text="Connexion initiale au brocker MQTT réussie...",
			parse_mode=ParseMode.HTML,
		)
	else:
		print("Connection failed")

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.

	client.subscribe("teslamate/cars/1/update_available")
	client.subscribe("teslamate/cars/1/doors_open")
	client.subscribe("teslamate/cars/1/usable_battery_level")
	client.subscribe("teslamate/cars/1/plugged_in")
	client.subscribe("teslamate/cars/1/time_to_full_charge")
	client.subscribe("teslamate/cars/1/locked")
	client.subscribe("teslamate/cars/1/state")
	client.subscribe("teslamate/cars/1/shift_state")
	client.subscribe("teslamate/cars/1/latitude")
	client.subscribe("teslamate/cars/1/longitude")
	client.subscribe("teslamate/cars/1/speed")
	client.subscribe("teslamate/cars/1/heading")

# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
	now = datetime.now()
	today = now.strftime("%d-%m-%Y %H:%M:%S")
	print(str(today)+" >> "+msg.topic+" : "+str(msg.payload.decode()))
	r = requests.get(api_url)
	jsonData = r.json()
	text_energie = "⚡️ : 🔋" if str(jsonData['plugged_in']) == "0" else "⚡️ : 🔌"
	lock_state = "🔐 verrouilée" if str(jsonData['locked']) == "1" else "🔓 déverrouilée"
	doors_state = "fermées" if str(jsonData['doors_open']) == "0" else "ouvertes"
	trunk_state = "fermé" if str(jsonData['trunk_open']) == "0" else "ouvert"
	clim_state = "éteinte" if str(jsonData['is_climate_on']) == "0" else "allumée"
	current_version = str(jsonData['version'])
	text_update = current_version+" ("+str(jsonData['update_version'])+")" if str(jsonData['update_available']) == "1" else current_version+" (à jour)"
	current_lat = float(jsonData['latitude'])
	current_long = float(jsonData['longitude'])
	send_current_location = False
	
	if msg.topic == "teslamate/cars/1/update_available" and str(msg.payload.decode()) == "true":
		text_state = "🎁 "+str(jsonData['state'])

	if msg.topic == "teslamate/cars/1/state":
		if str(msg.payload.decode()) == "online":
			text_state = "en ligne"
		elif str(msg.payload.decode()) == "asleep":
			text_state = "endormie"
		elif str(msg.payload.decode()) == "suspended":
			text_state = "en train de s'endormir..."
		elif str(msg.payload.decode()) == "charging":
			text_state = "en charge"
		elif str(msg.payload.decode()) == "offline":
			text_state = "éteinte/injoignable"
			send_current_location = True
		elif str(msg.payload.decode()) == "start":
			text_state = "en train de s'allumer..."
			send_current_location = True
		elif str(msg.payload.decode()) == "driving" and notif_conduite == True:
			text_state = "en conduite"
		else:
			print("Etat non pris en charge : "+str(msg.payload.decode()))

	if msg.topic == "teslamate/cars/1/time_to_full_charge":
		if str(jsonData['state']) == "charging":
			text_state = "en charge"
			temps_restant_mqtt = msg.payload.decode()
			if float(temps_restant_mqtt) > 1 and notif_charge == True:
				temps_restant_heure = int(temps_restant_mqtt)
				temps_restant_minute = round((float(temps_restant_mqtt) - temps_restant_heure) * 60,1)
				texte_minute = "minute." if temps_restant_minute < 2 else "minutes."
				if temps_restant_heure == 1:
					texte_temps = "⏳ "+str(temps_restant_heure)+" heure et "+str(temps_restant_minute)+" "+texte_minute
				elif temps_restant_heure == 0:
					texte_temps = "⏳ "+str(temps_restant_minute)+" "+texte_minute
				else:
					texte_temps = "⏳ "+str(temps_restant_heure)+" heures et "+str(temps_restant_minute)+" "+texte_minute
			if int(jsonData['usable_battery_level']) == int(jsonData['charge_limit_soc']):
				temps_restant = round(float(temps_restant_mqtt) * 60,2)
				temps_restant_minute = int(temps_restant)
				texte_minute = int(temps_restant)+" minute" if int(temps_restant) < 2 else " minutes"
				if float(temps_restant_mqtt) < 1:
					temps_restant_seconde = int((temps_restant - temps_restant_minute) * 60)
					texte_temps = "⏳ "+temps_restant_seconde+" secondes."
				else:
					texte_temps = "⏳ "+temps_restant+texte_minute
			if float(temps_restant_mqtt) == 0.0:
				texte_temps = "✅ Charge terminée."
			text_energie = "⚡️ : 🔌 "+texte_temps+"\nLimite à "+str(jsonData['charge_limit_soc'])+"%\nCharge ajoutée : "+str(jsonData['charge_energy_added'])+" kWh."

	if msg.topic == "teslamate/cars/1/locked" and notif_locked == True:
			if str(msg.payload.decode()) == "true" and str(jsonData['state']) != "asleep":
				send_current_location = True
				text_state = "verrouilléé"
			elif str(msg.payload.decode()) == "false":
				 text_state = "déverrouilléé"

	if msg.topic == "teslamate/cars/1/doors_open" and notif_porte == True:
		# if str(msg.payload.decode()) == "false":
		# 	text_state = "fermée"
		if str(msg.payload.decode()) == "true":
			text_state = "ouverte"

	text_msg = "🚙 "+str(jsonData['display_name'])+" est <b>"+text_state+"</b>\n🔋 : "+str(jsonData['usable_battery_level'])+"% ("+str(jsonData['est_battery_range_km'])+" km)\n"+text_energie+"\n"+lock_state+"\nPortes : "+doors_state+"\nCoffre : "+trunk_state+"\n🌡 intérieure : "+str(jsonData['inside_temp'])+"°c\n🌡 extérieure : "+str(jsonData['outside_temp'])+"°c\nClim : "+clim_state+"\nVersion : "+text_update+"\n"+str(today)

	bot.send_message(
		chat_id,
		text=str(text_msg),
		parse_mode=ParseMode.HTML,
	)

	if send_current_location == True:
		bot.send_location(
			chat_id,
			current_lat,
			current_long,
		)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(os.getenv('MQTT_BROKER_HOST', '127.0.0.1'),
			   int(os.getenv('MQTT_BROKER_PORT', 1883)), 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()


client.loop_start()  # start the loop
try:
	while True:
		time.sleep(1)

except KeyboardInterrupt:

	print("exiting")


client.disconnect()

client.loop_stop()
