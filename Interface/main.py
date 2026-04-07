#from mainInterface import App
from AppMap import app
from time import sleep


from MQTTClient import MQTTClient  
from customLogger import customLogger

ca_certs=r"C:\stage_HBO3_FMN\MQTT-container\emqx_setup\certs\ca_chain.pem"
certfile=r"C:\stage_HBO3_FMN\certificaten\GUI-cert.pem"
keyfile=r"C:\stage_HBO3_FMN\certificaten\GUI-key.pem"





if __name__ == "__main__":

    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")


    app = app()

    MQTTClient1 = MQTTClient("MQTTserver", 8883, "GUI", ca_certs, certfile, keyfile, on_message_handler=on_message)
    MQTTClient1.connectToBroker()


    MQTTClient1.listen_for_messages()
    sleep(0.1)
    MQTTClient1.subscribe_to_topic("Robots/")


    while True:
        pas=1+1
    #app.startGUI()