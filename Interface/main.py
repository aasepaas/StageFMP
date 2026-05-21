#from mainInterface import App
from calendar import setfirstweekday
from sqlite3 import SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE
from token import COMMA
from AppMap import app
from time import sleep
import customtkinter as ctk

from MQTTClient import MQTTClient  
from customLogger import customLogger
import math



ca_certs=r"C:\stage_HBO3_FMN\certificaten\ca_root.pem"
certfile=r"C:\stage_HBO3_FMN\certificaten\GUI-Na-CRL18-05-cert.pem"
keyfile=r"C:\stage_HBO3_FMN\certificaten\GUI-Na-CRL18-05-key.pem"

if __name__ == "__main__":

    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")

    MQTTClient1 = MQTTClient("localhost", 8883, "GUI", ca_certs, certfile, keyfile)
    app = app(MQTTClient1)

    MQTTClient1.SetMessageHandler(app.MessageHandler)
    MQTTClient1.connectToBroker()
    while not MQTTClient1.connectionStatus():
        pass

    MQTTClient1.listen_for_messages()
    sleep(1.1)
    MQTTClient1.subscribe_to_topic("Robots/#", qos=1)



    app.startGUI()