#from mainInterface import App

from AppMap import App
from time import sleep
from MQTTClient import MQTTClient  
import sys
from testrun import run_all_tests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / "certificaten"

ca_certs = CERT_DIR / "ca_root.pem"
certfile = CERT_DIR / "GUI-Na-CRL18-05-cert.pem"
keyfile  = CERT_DIR / "GUI-Na-CRL18-05-key.pem"

# ca_certs=r"C:\stage_HBO3_FMN\certificaten\ca_root.pem"
# certfile=r"C:\stage_HBO3_FMN\certificaten\GUI-Na-CRL18-05-cert.pem"
# keyfile=r"C:\stage_HBO3_FMN\certificaten\GUI-Na-CRL18-05-key.pem"

if __name__ == "__main__":

    # success = run_all_tests()
    # sys.exit(0 if success else 1)

    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")

    MQTTClient1 = MQTTClient("100.79.123.44", 8883, "GUI", ca_certs, certfile, keyfile)
    App = App(MQTTClient1)

    MQTTClient1.SetMessageHandler(App.MessageHandler)
    MQTTClient1.connectToBroker()
    while not MQTTClient1.connectionStatus():
        pass

    MQTTClient1.listen_for_messages()
    sleep(0.1)

    sleep(1.1)

    MQTTClient1.send_message(f"Robots/TestNaCRL18-05v1/status", "message random", qos=1)
    MQTTClient1.send_message(f"Commands/TestNaCRL18-05v1/MoveTo", "message random", qos=1)

    MQTTClient1.send_message(f"Robots/geenRobot1/status", "message random", qos=1)
    MQTTClient1.send_message(f"Commands/geenRobot1/MoveTo", "message random", qos=1)

    MQTTClient1.subscribe_to_topic("ajdajsdjaskd/#", qos=1)

    MQTTClient1.subscribe_to_topic("Robots/#", qos=1)




    App.startGUI()