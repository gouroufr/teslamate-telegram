#!/usr/bin/python
# -*- coding: utf-8 -*-
# By Gouroufr inspired by https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot
# Modified to be able to run without the API REST... we've got all infos we needed in the broker messages
# Add translation to texts : Open call for other languages !

# BETA version / copyleft Laurent alias gouroufr
version = "Version 20210507-04"

import os
import time
import math
import json
import requests
import paho.mqtt.client as mqtt
import pdb, traceback, sys

from datetime import datetime
from telegram.bot import Bot
from telegram.parsemode import ParseMode

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
usable_battery_level = -1 # not yet known
nouvelleinformation = False # global var to prevent redondant messages (is true only when new infos appears)
minbat=5  # minimum battery level that displays an alert message
doors_state = "❔"  # we don't know yet if doors are opened or closed
latitude = "❔"
longitude = "❔"
DEBUG = "❔"
UNITS = "❔"
distance = -1

# initializing the mandatory variables and cry if needed
if os.getenv('TELEGRAM_BOT_API_KEY') == None:
	print("Env Var missing ERROR : Please set the environment variable TELEGRAM_BOT_API_KEY and try again.")
	exit(1)
bot = Bot(os.getenv('TELEGRAM_BOT_API_KEY'))

if os.getenv('TELEGRAM_BOT_CHAT_ID') == None:
	print("Env Var missing ERROR : Please set the environment variable TELEGRAM_BOT_CHAT_ID and try again.")
	exit(1)
chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')


# initializing the recommended variables (not mandatory so we won't complain)
if os.getenv('LANGUAGE') == None:
	language = "EN"
else:
	language = os.getenv('LANGUAGE')

if os.getenv('CAR_ID') == None:
	CAR_ID = "1"  # more than one car is for rich people, so please donate... :-)
else: CAR_ID = os.getenv('CAR_ID')
if os.getenv('GPS') == None:
	
	GPS = False
else: GPS = True

if os.getenv('TIMESTAMP') == None: HORODATAGE = "bottom"
if os.getenv('TIMESTAMP') != None: HORODATAGE = os.getenv('TIMESTAMP').lower


# Km ou Miles choice
if os.getenv('UNITS') == None: UNITS = "Km"
if os.getenv('UNITS') != None and os.getenv('UNITS').lower == "km": UNITS = "Km"
if os.getenv('UNITS') != None and os.getenv('UNITS').lower == "miles": UNITS = "Miles"
if os.getenv('UNITS') != None and os.getenv('UNITS').lower == "metric": UNITS = "Km"
if os.getenv('UNITS') != None and os.getenv('UNITS').lower == "imperial": UNITS = "Miles"

if os.getenv('DEBUG') != None: DEBUG = os.getenv('DEBUG')
if DEBUG == "True": DEBUG = True
else: DEBUG = False

# Status print
print ("--------------------------------------------")
print("Env Var CAR_ID    : " + CAR_ID)
print("Env Var LANGUAGE  : " + language)
print("Env Var GPS       : " + str(GPS))
print("Env Var TIMESTAMP : " + str(HORODATAGE))
print("Env Var UNITS     : " + UNITS)
print('Mode DEBUG        : '+str(DEBUG))
print ("--------------------------------------------" + crlf)

# Text translation depends on a 2 letters code : 
# FR : Français
# EN : English
# SP : -not implemented-
# Call for volunteers => Please provide PR with other languages
if language == "FR":
	contobroker = "✔️ connecté au broker MQTT avec succès"+crlf+version
	brokerfailed = "❌ échec de connexion au broker MQTT"
	majdispo = "🎁 une mise à jour est disponible"
	etatendormie = "💤 est endormie"
	etatonline = "📶 est connectée"
	etatsuspend = "🛏️ cherche à s'endormir"
	etatcharge = "🔌 se recharge"
	etatoffline = "🛰️ n'est pas connectée au réseau"
	etatstart = "🚀 démarre ses systèmes"
	etatdrive = "🏁 roule"
	etatunk = "⭕ état inconnu"
	heure = "heure"     
	minute = "minute"
	plurialsuffix = "s" 
	chargeterminee = "✅ charge terminée"
	energieadded = "⚡️ 000 kWh ajoutés"  # Keep the 000 in the string, a replace is made with real value
	carislocked = "🔐 est verrouillée"
	carisunlocked = "🔓 est déverrouillée"
	lowbattery="Batterie faible"
	dooropened="🕊️ Porte(s) ouverte(s)"
	doorclosed="☑️ Portes fermées"
elif language == "SP":
	print("SPANISH language not available yet") # No text translation available would send empty messages, so we end here
	exit(1)                                     # implemented here as an example for Pull Requests for additionnal languages
else:
	contobroker = "✔️ successfully connected to MQTT broker"
	brokerfailed = "❌ Failed to connect to MQTT broker"
	majdispo = "🎁 An update is available"
	etatendormie = "💤 is asleep"
	etatonline = "📶 is online"
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
	dooropened="🕊️ Door(s) opened"
	doorclosed="☑️ Doors closed"

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
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/display_name")         # Call it the way you like
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/model")                # Either "S", "3", "X" or "Y"
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/odometer")             # in Km (todo conv in Miles for imperial fans) 
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/update_available")     # Gift ?
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/state")                # Dans quel état j'ère
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/locked")			    # boolean
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/exterior_color")       # usefull ! 
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/charge_energy_added")  # in KwH
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/doors_open")			# Boolean
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/usable_battery_level") # percent
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/plugged_in")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/time_to_full_charge")  # Hours
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/shift_state")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/latitude")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/longitude")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/speed")
	client.subscribe("teslamate/cars/"+str(CAR_ID)+"/est_battery_range_km")
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
		global doorclosed
		global dooropened
		global doors_state
		global distance
		global DEBUG
		global GPS
		global HORODATAGE
		global CAR_ID
		global UNITS
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
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/usable_battery_level": usable_battery_level = float(msg.payload.decode())  # Car is moving, don't bother the driver
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/est_battery_range_km": distance = math.floor(float(msg.payload.decode()))              # estimated range
		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/time_to_full_charge":                                                    # Collect infos but don't send a message NOW
			temps_restant_mqtt = str(msg.payload.decode())
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



		if msg.topic == "teslamate/cars/"+str(CAR_ID)+"/doors_open":
			if str(msg.payload.decode()) == "false": doors_state = doorclosed
			elif str(msg.payload.decode()) == "true": doors_state = dooropened


		if nouvelleinformation == True:
			# Do we have enough informations to send a complete message ?
			# if pseudo != "❔" and model != "❔" and etat_connu != "❔" and locked != "❔" and usable_battery_level != "❔" and latitude != "❔" and longitude != "❔" and distance > 0:
			if distance > 0:
				if HORODATAGE == "top": text_msg = str(today) + crlf + pseudo+" ("+model+") "+str(km)+" km"+crlf+text_locked+crlf+etat_connu+crlf
				else: text_msg = pseudo+" ("+model+") "+str(km)+" km"+crlf+text_locked+crlf+etat_connu+crlf
				if DEBUG: print("According to HORODATAGE var (" + HORODATAGE + ") the resulting message to the bot is at this step :" + crlf + text_msg + crlf)

				# Do we have some special infos to add to the standard message ?
				if doors_state != "❔": text_msg = text_msg+doors_state+crlf
				if etat_connu == str(etatcharge) and temps_restant_charge == chargeterminee: text_msg = text_msg+chargeterminee+crlf
				if etat_connu == str(etatcharge) and temps_restant_charge != "❔": text_msg = text_msg+temps_restant_charge+crlf
				if int(usable_battery_level) > minbat and int(usable_battery_level) != -1 :text_msg = text_msg+"🔋 "+str(usable_battery_level)+" %"+crlf
				elif int(usable_battery_level) != -1: text_msg = text_msg+"🛢️ "+str(usable_battery_level)+" % "+lowbattery+crlf
				if distance > 0 and UNITS == "km": text_msg = text_msg+"🏎️ "+str(math.floor(distance))+" Km"+crlf
				if distance > 0 and UNITS == "miles": text_msg = text_msg+"🏎️ "+str(math.floor(distance/1.609))+" miles"+crlf


				# GPS location (googlemap)
				if GPS: text_msg = text_msg + "https://www.google.fr/maps/?q="+str(latitude)+","+str(longitude)+crlf
				if DEBUG: print("According to GPS var (" + str(GPS) + ") the resulting message to the bot is at this step :" + crlf + text_msg + crlf)

				# bottom HORODATAGE the message if needed
				if HORODATAGE == "bottom": text_msg = text_msg+crlf+str(today)
				if DEBUG: print("According to HORODATAGE var (" + HORODATAGE + ") the resulting message to the bot is at this step :" + crlf + text_msg + crlf)				

				# Send the message
				if DEBUG == True and distance > 0: print("DEBUG : Message sent to Telegram Bot : " + crlf + "-----------------------" +crlf +str(text_msg) + crlf + "-----------------------" + crlf)
				if distance > 0: bot.send_message(chat_id,text=str(text_msg),parse_mode=ParseMode.HTML,)
				nouvelleinformation = False  # we reset this to false since we've just sent an update to the user
				del temps_restant_charge     # reset the computed time to full charge to unkown state to prevent redondant and not updated messages
				temps_restant_charge = "❔"  # reset the computed time to full charge to unkown state to prevent redondant and not updated messages


	except: # catch *all* exceptions
		e = sys.exc_info()
		print(e) # (Exception Type, Exception Value, TraceBack)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set
if os.getenv('MQTT_BROKER_USERNAME') == None:
    pass
else:
    if os.getenv('MQTT_BROKER_PASSWORD') == None:
        client.username_pw_set(os.getenv('MQTT_BROKER_USERNAME', ''))
    else:
        client.username_pw_set(os.getenv('MQTT_BROKER_USERNAME', ''), os.getenv('MQTT_BROKER_PASSWORD', ''))


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
