from time import sleep
from MQTTClient import MQTTClient  
from customLogger import customLogger

ca_certs=r"C:\stage_HBO3_FMN\MQTT-container\emqx_setup\certs\ca_chain.pem"
certfile=r"C:\stage_HBO3_FMN\certificaten\client-cert01.pem"
keyfile=r"C:\stage_HBO3_FMN\certificaten\client-key01.pem"


# def __init__(self, brokerINC, portINC, client_idINC, ca_certs, certfile, keyfile, topicINC = None):

if __name__ == '__main__':
   
    logger = customLogger()
    def mijn_message_handler(client, userdata, msg):
        bericht = msg.payload.decode()
        topic = msg.topic
    
        print(f"Bericht ontvangen op '{topic}': {bericht}")
    
        # if statements op berichten
        if topic == "sensors/temperature":
            temperatuur = float(bericht)
            msgSent = False
            if temperatuur > 30:
                print("WAARSCHUWING: Temperatuur te hoog!")
                if msgSent:
                    msgSent = False
                else:
                    MQTTClient1.send_message("emqx/secure/communication", "KIJK UIT TE WARM")
    
        elif topic == "commands/led":
            if bericht == "ON":
                print("LED aan zetten")
            elif bericht == "OFF":
                print("LED uit zetten")
        
    logger.setWaarde("baka")
    MQTTClient1 = MQTTClient("MQTTserver", 8883, "pythonClient01", ca_certs, certfile, keyfile,on_message_handler=mijn_message_handler)
    MQTTClient1.connectToBroker()
    logger.setWaarde("ajndjakjsa")
    MQTTClient2  = MQTTClient("MQTTserver", 8883, "pythonClient22", ca_certs, certfile, keyfile,on_message_handler=mijn_message_handler)
    MQTTClient2.connectToBroker()


    MQTTClient1.listen_for_messages()
    MQTTClient2.listen_for_messages()
    sleep(0.1)

    logger.prCyan(MQTTClient1 == MQTTClient2)


    MQTTClient1.subscribe_to_topic("emqx/secure/communication")
    MQTTClient1.subscribe_to_topic("sensors/temperature")
    MQTTClient1.subscribe_to_topic("commands/led")

    MQTTClient2.subscribe_to_topic("commands/led")


    MQTTClient1.send_message("emqx/secure/communication", "hoibericht")
    sleep(5)
    MQTTClient1.send_message("sensors/temperature", "31")
    sleep(5)
    MQTTClient1.send_message("commands/led", "ON")
    MQTTClient2.send_message("commands/led", "ON")
    sleep(5)
    MQTTClient1.send_message("commands/led", "NIKS")
    sleep(5)
    MQTTClient1.send_message("commands/led", "OFF")
    sleep(10)

    MQTTClient1.disconnect_client()
    MQTTClient2.disconnect_client()




