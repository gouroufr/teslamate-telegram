# teslamate-telegram

This is a TESLAMATE complement that sends updates to a Telegram chat.


Environnement variables : 

      - MQTT_BROKER_HOST=mosquitto_IP                  # IP or FQDN 
      - MQTT_BROKER_PORT=mosquitto_PORT                # (default 1883)
      - TELEGRAM_BOT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx   # See Telegram doc
      - TELEGRAM_BOT_CHAT_ID=xxxxxxxxxxxxxx            # See Telegram doc
      - LANGUAGE=EN                                    # FR (french) is also available (default ENglish)
      - GPS=True                                       # or False : includes car location map in Telegram message, default False
      - CAR_ID=1                                       # Your "n"th Tesla car in your inventory... default 1st one



Example of a docker-compose for the full suite of teslamate containers including this Telegram bot :
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
      - MQTT_BROKER_PORT=mosquitto_PORT                # (default 1883)
      - TELEGRAM_BOT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx   # See Telegram doc https://core.telegram.org/
      - TELEGRAM_BOT_CHAT_ID=xxxxxxxxxxxxxx            # See Telegram doc https://core.telegram.org/
      - LANGUAGE=EN                                    # FR (french) is also available (default ENglish)
      - GPS=True                                       # or False : includes car location map in Telegram message, default False
      - CAR_ID=1                                       # Your "n"th car in your Tesla's inventory... default 1st one

volumes:
  teslamate-db:
  teslamate-grafana-data:
  mosquitto-conf:
  mosquitto-data:

```


*** Licence and donations : ***

All is free software under GPL licence.

Donations are welcome :

send bitcoins to 15DbfoLVmJ1iwHGnaeB25NBD2kE393XZZD or register and have fun (Caution: it's free, so you'll never become rich !) for free with this referral link : https://freebitco.in/?r=36618348&tag=ghteslamatetg
