#!/usr/bin/python
# -*- coding: utf-8 -*-
# By Gouroufr inspired by https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot
# Modified to be able to run without the API REST... we've got all infos we needed in the broker messages
# Add translation to texts : Open call for other languages !
# version 0.7 on april 13th, 2021 / copyleft Laurent alias gouroufr

import os
import time
from datetime import datetime
import json
import requests

import paho.mqtt.client as mqtt

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# Static variables
crlf = "\n"
pseudo = "❔" # not yet known
model  = "❔" # not yet known
km = "❔" # not yet known
ismaj = "❔" # not yet known
etat_connu = "❔" # not yet known
locked = "❔" # not yet known
temps_restant_charge = "❔" # not yet known
text_energie = "❔" # not yet known

# initializing the mandatory variables and cry if needed
if os.getenv('TELEGRAM_BOT_API_KEY') == None:
	print("Error: Please set the environment variable TELEGRAM_BOT_API_KEY and try again.")
	exit(1)
bot = Bot(os.getenv('TELEGRAM_BOT_API_KEY'))

if os.getenv('TELEGRAM_BOT_CHAT_ID') == None:
	print("Error: Please set the environment variable TELEGRAM_BOT_CHAT_ID and try again.")
	exit(1)
chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')


# initializing the recommended variables (not mandatory so we won't complain)
if os.getenv('LANGUAGE') == None:
	print("No language selected, using ENglish as default." + crlf + "Currently available languages : EN, FR" + crlf + "Please set LANGUAGE in environnement variables.")
	language = "EN"
else:
	language = os.getenv('LANGUAGE')
if os.getenv('CAR_ID') == None:
	print("No car identifier set, using first car in your Telsa account as default one." + crlf + "Please set CAR_ID if needed in environnement variables.")
	CAR_ID = "1"  # more than one car is for rich people, so please donate... :-)
else:
	CAR_ID = os.getenv('CAR_ID')
	# should test if entry is a number... (btw what is the max ?)

	# TODO : add the Km ou Miles choice

# Text translation depends on a 2 letters code : 
# FR : Français
# EN : English
# SP : -not implemented-
# Call for volunteers => Please provide PR with other languages
if language == "FR":
	print("FRENCH language set")
	contobroker = "✔️ connecté au broker MQTT avec succès"
	brokerfailed = "❌ échec de connexion au broker MQTT"
	majdispo = "🎁 une mise à jour est disponible"
	etatendormie = "💤 est endormie"
	etatonline = "✨ est connectée"
	etatsuspend = "🛏️ cherche à s'endormir"
	etatcharge = "🔌 se recharge"
	etatoffline = "🛰️ n'est pas connectée au réseau"
	etatstart = "🚀 démarre ses systèmes"
	etatdrive = "🏁 est en circulation"
	etatunk = "⭕ état inconnu"
	heure = "heure"     
	minute = "minute"
	plurialsuffix = "s" 
	chargeterminee = "✅ charge terminée"
	energieadded = "⚡️ 000 KwH ajoutés"
	carislocked = "🔐 est verrouilée"
	carisunlocked = "🔓 est déverrouilée"

elif language == "SP":
	print("SPANISH language not available yet") # No text translation available would send empty messages, so we end here
	exit(1)
else:
	print("ENGLISH language set")
	contobroker = "✔️ successfully connected to MQTT broker"
	brokerfailed = "❌ Failed to connect to MQTT broker"
	majdispo = "🎁 An update is available"
	etatendormie = "💤 is asleep"
	etatonline = "✨ is online"
	etatsuspend = "🛏️ trying to sleep"
	etatcharge = "🔌 is charging"
	etatoffline ="🛰️ is not connected"
	etatstart = "🚀 is starting"
	etatdrive = "🏁 is driving"
	etatunk = "⭕ Unknown state"
	heure = "hour"    
	minute = "minute" 
	plurialsuffix = "s" 
	chargeterminee = "✅ charge ended"
	energieadded = "⚡️ 000 KwH added"  # Keep the 000 in the string, a replace is made with real value
	carislocked = "🔐 is locked"
	carisunlocked = "🔓 is unlocked"



# Fully based on example from https://pypi.org/project/paho-mqtt/
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print(contobroker)
		bot.send_message(chat_id,text=contobroker,parse_mode=ParseMode.HTML)
	else:
		print(brokerfailed)
		bot.send_message(chat_id,text=brokerfailed,parse_mode=ParseMode.HTML)


	# Subscribing in on_connect() means that if we lose the connection and reconnect subscriptions will be renewed.
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/display_name")        # Call it the way you like
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/model")               # Either "S", "3", "X" or "Y"
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/odometer")            # in Km (todo conv in Miles for imperial fans) 
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/update_available")    # Gift ?
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/state")               # Dans quel état j'ère
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/locked")			   # boolean
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/exterior_color")      # usefull ! 
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/charge_energy_added") # in KwH
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/doors_open")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/usable_battery_level")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/plugged_in")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/time_to_full_charge")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/shift_state")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/latitude")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/longitude")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/speed")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/heading")

# Overcharging static variables with infos collected each round
def on_message(client, userdata, msg):
	now = datetime.now()
	today = now.strftime("%d-%m-%Y %H:%M:%S")
	print(str(today)+" >> "+str(msg.topic)+" : "+str(msg.payload.decode()))
	print(text_msg)
	print("...")

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/display_name":
		print("aaaaahhhhh.....")
		pseudo = "🚗 "+str(msg.payload.decode())
		print(pseudo)

	if msg.topic == "teslamate/cars/1/display_name":
		pseudo = "🚗 "+str(msg.payload.decode())
		print(pseudo)		


	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/model":
		model = "Model "+str(msg.payload.decode())

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/odometer":
		km = str(msg.payload.decode())

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/update_available":
		ismaj = str(msg.payload.decode())

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/state":
		if str(msg.payload.decode()) == "online":
			etat_connu = str(etatonline)
		elif str(msg.payload.decode()) == "asleep":
			etat_connu = str(etatendormie)
		elif str(msg.payload.decode()) == "suspended":
			etat_connu = str(etatsuspend)
		elif str(msg.payload.decode()) == "charging":
			etat_connu = str(etatcharge)
		elif str(msg.payload.decode()) == "offline":
			etat_connu = str(etatoffline)
		elif str(msg.payload.decode()) == "start":
			etat_connu = str(etatstart)
		elif str(msg.payload.decode()) == "driving":
			etat_connu = str(etatdrive)
		else:
			etat_connu = str(etatunk)

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/locked":
		locked = "Model "+str(msg.payload.decode())
		if str(locked) == "true": text_locked = carislocked
		if str(locked) == "false": text_locked = carisunlocked
		

	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/time_to_full_charge":
		temps_restant_mqtt = msg.payload.decode()
		if float(temps_restant_mqtt) > 1:
			temps_restant_heure = int(temps_restant_mqtt)
			temps_restant_minute = round((float(temps_restant_mqtt) - temps_restant_heure) * 60,1)
			texte_minute = minute if temps_restant_minute < 2 else minute + "" + plurialsuffix
			if temps_restant_heure == 1:
				temps_restant_charge = "⏳ "+str(temps_restant_heure)+" " + heure + " "+str(temps_restant_minute)+" "+texte_minute
			elif temps_restant_heure == 0:
				temps_restant_charge = "⏳ "+str(temps_restant_minute)+" "+texte_minute
			else:
				temps_restant_charge = "⏳ "+str(temps_restant_heure)+" " + heure +"" + plurialsuffix + " "+str(temps_restant_minute)+" "+texte_minute

		if float(temps_restant_mqtt) == 0.0:
			temps_restant_charge = chargeterminee


	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/charge_energy_added":
		kwhadded = msg.payload.decode()
		text_energie = energieadded.replace("000", str(kwhadded))


	if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/doors_open" and notif_porte == True:
		# if str(msg.payload.decode()) == "false":
		# 	text_state = "fermée"
		if str(msg.payload.decode()) == "true":
			text_state = "ouverte"

	#	text_msg = "🚙 "+str(jsonData['display_name'])+" est <b>"+text_state+"</b>\n🔋 : "+str(jsonData['usable_battery_level'])+"% ("+str(jsonData['est_battery_range_km'])+" km)\n"+text_energie+"\n"+lock_state+"\nPortes : "+doors_state+"\nCoffre : "+trunk_state+"\n🌡 intérieure : "+str(jsonData['inside_temp'])+"°c\n🌡 extérieure : "+str(jsonData['outside_temp'])+"°c\nClim : "+clim_state+"\nVersion : "+text_update+"\n"+str(today)
	text_msg = "🚙 "+pseudo+" ("+model+")"+crlf+"\
		"+etat_connu+crlf+"\
			"+str(today)

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

client.connect(os.getenv('MQTT_BROKER_HOST', '127.0.0.1'),int(os.getenv('MQTT_BROKER_PORT', 1883)), 60)


client.loop_start()  # start the loop
try:
	while True:
		time.sleep(1)

except KeyboardInterrupt:
	print("exiting")

# au revoir...
client.disconnect()
client.loop_stop()
