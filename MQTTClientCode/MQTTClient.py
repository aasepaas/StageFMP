import random
import ssl
from paho.mqtt import client as mqtt_client

from virtualMQTTClient import VirtualMQTTclient

from customLogger import customLogger

class MQTTClient(VirtualMQTTclient):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, brokerINC, portINC, client_idINC, ca_certs, certfile, keyfile, on_message_handler=None, topicINC = None):
        if hasattr(self, "startLoop"):
            self.logger.prRed("Helaas object bestaat al")
            print(self.logger.getWaarde())
            return
        self.broker_address = brokerINC
        self.port = portINC
        self.topic = topicINC
        self.client_id = client_idINC
        self.MQTTClientLib = mqtt_client.Client(self.client_id)
        self.connected = False
        self.startLoop = False

        self.MQTTClientLib.on_connect = self._on_connect_callback
        
        # Assign a custom message handler or use the default one
        if on_message_handler:
            self.MQTTClientLib.on_message = on_message_handler
        else:
            self.MQTTClientLib.on_message = self._on_message_callback
        # mTLS certificate paths
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile
        self.logger = customLogger()
        print(self.logger.getWaarde())

        self.logger.prPurple("Nieuwe object aangemaakt")

        


    def _on_connect_callback(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            print(f"Subscriber client '{self.client_id}' connected successfully to the broker!")
        else:
            print(f"Subscriber client '{self.client_id}' failed to connect, return code: {rc}")

    def connectToBroker(self):
        """Configures TLS settings and connects to the broker."""
        if not self.connected:
            if self.ca_certs and self.certfile and self.keyfile:
                # Set up the mTLS connection
                self.MQTTClientLib.tls_set(
                    ca_certs=self.ca_certs,
                    certfile=self.certfile,
                    keyfile=self.keyfile,
                    cert_reqs=ssl.CERT_REQUIRED, # Require peer certificate verification
                    tls_version=ssl.PROTOCOL_TLS
                )
                self.connected = True
            else:
                return False
            
            self.MQTTClientLib.connect(self.broker_address, self.port, 60)


    def sendToBroker(self):
        pass

    def receiveFromBroker(self):
        pass


    def subscribe_to_topic(self, topic):
        """Subscribes the client to a specified topic."""
        self.MQTTClientLib.subscribe(topic)
        print(f"Subscriber client '{self.client_id}' is now subscribed to topic '{topic}'")

    def _on_message_callback(self, MQTTClientLib, userdata, msg):
        """The default callback for receiving messages."""
        print(f"Subscriber client '{self.client_id}' received message from topic '{msg.topic}': {msg.payload.decode()}")

    def listen_for_messages(self):
        """Starts a threaded loop to listen for incoming messages."""
        """This is non-blocking!!"""
        if self.connected and not self.startLoop:
            self.MQTTClientLib.loop_start()
            self.startLoop = True

    def disconnect_client(self):
        """Disconnects the client from the broker."""
        if self.connected:
            self.MQTTClientLib.disconnect()
            self.connected = False

    def connectionStatus(self):
        return self.connected

    def send_message(self, topic, payload):
        """Publishes a message to a given topic."""
        self.MQTTClientLib.publish(topic, payload)
        print(f"Publisher client '{self.client_id}' sent message to topic '{topic}': {payload}")
