# teslamate-telegram

This is a TESLAMATE complement (addon) that sends updates to a Telegram chat.
It reads a MQTT broker for messages about TESLA car and sends correlated informations via a Telegram bot to it's owner.


Environnement variables : 
```
      - MQTT_BROKER_HOST=mosquitto_IP                  # IP or FQDN 
      - MQTT_BROKER_PORT=mosquitto_PORT                # (optional) default 1883
      - MQTT_BROKER_USERNAME=username                  # (optional)
      - MQTT_BROKER_PASSWORD=password                  # (optional)
      - TELEGRAM_BOT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx   # See Telegram doc https://core.telegram.org/
      - TELEGRAM_BOT_CHAT_ID=xxxxxxxxxxxxxx            # See Telegram doc https://core.telegram.org/
      - LANGUAGE=EN                                    # (optional) FR (french) / EN (English - default) / Please PR for other languages / [EN|FR]
      - GPS=True                                       # (optional) includes car location map in Telegram message, default False [True|False]
      - CAR_ID=1                                       # (optional) Your "n"th car in your Tesla's inventory... default 1st one [1-9]
      - TIMESTAMP=bottom                               # (optional) prints the date at the [bottom|top|none] of each message, none won't prints it
      - UNITS=Km                                       # (optional) Metric or Imperial measurement display [Km|Miles] or [Metric|Imperial] metric defaults
      - DEBUG=True                                     # (optional) Display on console the bot messages / default is false
```


Example of a docker-compose for the full suite of Teslamate containers including this Telegram bot :
```
version: "3"

services:
  teslamate:
    image: teslamate/teslamate:latest
    restart: always
    environment:
      - DATABASE_USER=teslamate  # to be changed
      - DATABASE_PASS=secret     # to be changed
      - DATABASE_NAME=teslamate  # to be changed
      - DATABASE_HOST=database
      - MQTT_HOST=mosquitto
    ports:
      - 4000:4000
    volumes:
      - ./import:/opt/app/import
    cap_drop:
      - all

  database:
    image: postgres:12
    restart: always
    environment:
      - POSTGRES_USER=teslamate  
      - POSTGRES_PASSWORD=secret # to be changed
      - POSTGRES_DB=teslamate    
    volumes:
      - teslamate-db:/var/lib/postgresql/data

  grafana:
    image: teslamate/grafana:latest
    restart: always
    environment:
      - DATABASE_USER=teslamate 
      - DATABASE_PASS=secret    # to be changed
      - DATABASE_NAME=teslamate # to be changed
      - DATABASE_HOST=database  # to be changed
    ports:
      - 3000:3000
    volumes:
      - teslamate-grafana-data:/var/lib/grafana

  mosquitto:
    image: eclipse-mosquitto:1.6
    restart: always
    ports:
      - 1883:1883
    volumes:
      - mosquitto-conf:/mosquitto/config
      - mosquitto-data:/mosquitto/data
      
  telegrambot:
    image: gouroufr/teslamate-telegram:latest
    restart: always
    environment:
      - MQTT_BROKER_HOST=mosquitto_IP                  # IP or FQDN 
      - MQTT_BROKER_PORT=mosquitto_PORT                # (optional) default 1883
      - MQTT_BROKER_USERNAME=username                  # (optional)
      - MQTT_BROKER_PASSWORD=password                  # (optional)
      - TELEGRAM_BOT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx   # See Telegram doc https://core.telegram.org/
      - TELEGRAM_BOT_CHAT_ID=xxxxxxxxxxxxxx            # See Telegram doc https://core.telegram.org/
      - LANGUAGE=EN                                    # (optional) FR (french) / EN (English - default) / Please PR for other languages / [EN|FR]
      - GPS=True                                       # (optional) includes car location map in Telegram message, default False [True|False]
      - CAR_ID=1                                       # (optional) Your "n"th car in your Tesla's inventory... default 1st one [1-9]
      - TIMESTAMP=bottom                               # (optional) prints the date at the [bottom|top|none] of each message, none won't prints it
      - UNITS=Km                                       # (optional) Metric or Imperial measurement display [Km|Miles] or [Metric|Imperial] metric defaults
      - DEBUG=True                                     # (optional) Display on console the bot messages / default is false

volumes:
  teslamate-db:
  teslamate-grafana-data:
  mosquitto-conf:
  mosquitto-data:

```


*** Licence and donations : ***

All is free software under GPL licence.

Donations are welcome :

Send bitcoins to 15DbfoLVmJ1iwHGnaeB25NBD2kE393XZZD
Register and play/have fun/win a few satoshi for free here with this referral link : https://freebitco.in/?r=36618348
Help people around you
Give a dog a new life (adoption)
Save a licorn
... :-)