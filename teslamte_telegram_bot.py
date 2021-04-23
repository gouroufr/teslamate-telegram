#!/usr/bin/python
# -*- coding: utf-8 -*-
# By Gouroufr inspired by https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot
# Modified to be able to run without the API REST... we've got all infos we needed in the broker messages
# Add translation to texts : Open call for other languages !
# BETA version 0.7 on april 13th, 2021 / copyleft Laurent alias gouroufr

version = "Version 2021041601"

import os
import time
from datetime import datetime
import json
import requests

import paho.mqtt.client as mqtt

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# debug
import pdb, traceback, sys
debug = False  # internal use, should be deleted before or at least false when going to production/publish
send_current_location = False

# Static variables
crlf = "\n"
pseudo = "❔" # not yet known
model  = "❔" # not yet known
km = "❔" # not yet known
ismaj = "❔" # not yet known
etat_connu = "❔" # not yet known
locked = "❔" # not yet known
text_locked = "❔" # not yet known
temps_restant_charge = "❔" # not yet known
text_energie = "❔" # not yet known
usable_battery_level = "❔" # not yet known
nouvelleinformation = False # global var to prevent redondant messages (is true only when new infos appears)
minbat=5  # minimum battery level to not display alert message

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
	contobroker = "✔️ connecté au broker MQTT avec succès"+crlf+version
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
	energieadded = "⚡️ 000 kWh ajoutés"  # Keep the 000 in the string, a replace is made with real value
	carislocked = "🔐 est verrouilée"
	carisunlocked = "🔓 est déverrouilée"
	lowbattery="Batterie faible"
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
	energieadded = "⚡️ 000 kWh added"  # Keep the 000 in the string, a replace is made with real value
	carislocked = "🔐 is locked"
	carisunlocked = "🔓 is unlocked"
	lowbattery="Low battery"


# Partially based on example from https://pypi.org/project/paho-mqtt/
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
	try:
		global pseudo 
		global model
		global km
		global ismaj
		global etat_connu
		global locked 
		global text_locked 
		global temps_restant_charge
		global text_energie
		global nouvelleinformation
		global latitude
		global longitude
		global usable_battery_level
		now = datetime.now()
		today = now.strftime("%d-%m-%Y %H:%M:%S")
		print(str(today)+" >> "+str(msg.topic)+" : "+str(msg.payload.decode()))


		# Do not send any messages :
		# --------------------------
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/display_name": pseudo = "🚗 "+str(msg.payload.decode())                 # do we change name often ?
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/model": model = "Model "+str(msg.payload.decode())                       # Model is very static...
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/odometer": km = str(msg.payload.decode())                                # Car is moving, don't bother the driver
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/latitude": latitude = str(msg.payload.decode())                          # Car is moving, don't bother the driver
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/longitude": longitude = str(msg.payload.decode())                        # Car is moving, don't bother the driver
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/usable_battery_level": usable_battery_level = str(msg.payload.decode())  # Car is moving, don't bother the driver
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/time_to_full_charge":                                                    # Collect infos but don't send a message NOW
			temps_restant_mqtt = msg.payload.decode()
			if float(temps_restant_mqtt) > 1:
				nouvelleinformation = True     # Exception : send an update each time we get an updated ETA to full charge (debug)
				temps_restant_heure = int(float(temps_restant_mqtt))
				temps_restant_minute = int(float(round((float(temps_restant_mqtt) - temps_restant_heure) * 60,1)))
				texte_minute = minute if temps_restant_minute < 2 else minute + "" + plurialsuffix
				if temps_restant_heure == 1:
					temps_restant_charge = "⏳ "+str(temps_restant_heure)+" " + heure + " "+str(temps_restant_minute)+" "+texte_minute
				elif temps_restant_heure == 0:
					temps_restant_charge = "⏳ "+str(temps_restant_minute)+" "+texte_minute
				else:
					temps_restant_charge = "⏳ "+str(temps_restant_heure)+" " + heure +"" + plurialsuffix + " "+str(temps_restant_minute)+" "+texte_minute
			if int(float(temps_restant_mqtt) * 60 ) == 0:
				temps_restant_charge = chargeterminee
				nouvelleinformation = True     # Exception : We should tell the user the car is charged

		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/charge_energy_added":                                                  # Collect infos but don't send a message NOW
			kwhadded = msg.payload.decode()
			text_energie = energieadded.replace("000", str(kwhadded))


		
		# Please send me a message :
		# --------------------------
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/update_available":
			if ismaj != str(msg.payload.decode()):
				ismaj = str(msg.payload.decode())
				nouvelleinformation = True
	
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/state":
			if str(msg.payload.decode()) == "online":
				if etat_connu != str(etatonline):
					etat_connu = str(etatonline)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "asleep":
				if etat_connu != str(etatendormie):
					etat_connu = str(etatendormie)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "suspended":
				if etat_connu != str(etatsuspend):
					etat_connu = str(etatsuspend)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "charging":
				if etat_connu != str(etatcharge):
					etat_connu = str(etatcharge)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "offline":
				if etat_connu != str(etatoffline):
					etat_connu = str(etatoffline)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "start":
				if etat_connu != str(etatstart):
					etat_connu = str(etatstart)
					nouvelleinformation = True
			elif str(msg.payload.decode()) == "driving":
				if etat_connu != str(etatdrive):
					etat_connu = str(etatdrive)
					nouvelleinformation = True				
				etat_connu = str(etatdrive)
			else:
				etat_connu = str(etatunk)  # do not send messages as we don't know what to say, keep quiet and move on... :)

		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/locked":              # interesting info but at initial startup it gives 1 message for state and 1 message for lock
			if locked != str(msg.payload.decode()):                           # We should add a one time pointer to avoid this (golobal)
				locked = str(msg.payload.decode())
				nouvelleinformation = True
				if str(locked) == "true": text_locked = carislocked
				if str(locked) == "false": text_locked = carisunlocked




		# awaiting translation code modification	  	
		#if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/doors_open":
			# if str(msg.payload.decode()) == "false":
			# 	text_state = "fermée"
			#if str(msg.payload.decode()) == "true":
			#	text_state = "ouverte"



		if nouvelleinformation:
			# Do we have enough informations to send a complete message ?
			if pseudo != "❔" and model != "❔" and etat_connu != "❔" and locked != "❔" and usable_battery_level != "❔":
				# standard message
				text_msg = pseudo+" ("+model+") "+str(km)+" km"+crlf+text_locked+crlf+etat_connu+crlf
				# Do we have some special infos to add to the standard message ?
				if etat_connu == str(etatcharge) and temps_restant_charge == chargeterminee: text_msg = text_msg+chargeterminee+crlf
				if etat_connu == str(etatcharge) and temps_restant_charge != "❔": text_msg = text_msg+temps_restant_charge+crlf
				if usable_battery_level != "❔" and int(usable_battery_level) > minbat:text_msg = text_msg+"🔋 "+usable_battery_level+" %"+crlf
				else: text_msg = text_msg+"🛢️ "+usable_battery_level+" % "+lowbattery+crlf


					
				# timestamp to the message
				text_msg = text_msg+crlf+str(today)

				# Send the message
				bot.send_message(chat_id,text=str(text_msg),parse_mode=ParseMode.HTML,)
				nouvelleinformation = False  # we reset this to false since we've just sent an update to the user
				temps_restant_charge = "❔"  # reset the computed time to full charge to unkown state to prevent redondant and not updated messages

				#	"<a href='https://www.google.fr/maps/?q="+str(latitude)+","+str(longitude)+"'Localisation</a>"+crlf+"\    need to find out a way to send a map
				if send_current_location == True:
					bot.send_location(
						chat_id,
						latitude,
						longitude
					)
	except: # catch *all* exceptions
		e = sys.exc_info()
		print(e) # (Exception Type, Exception Value, TraceBack)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message


client.connect(os.getenv('MQTT_BROKER_HOST'),int(os.getenv('MQTT_BROKER_PORT', 1883)), 60)
client.loop_start()  # start the loop
try:

	while True:
		time.sleep(1)

except:
        extype, value, tb = sys.exc_info()
        traceback.print_exc()
        # pdb.post_mortem(tb)

#except KeyboardInterrupt:
#	print("exiting")

# au revoir...
client.disconnect()
client.loop_stop()
