import random
import ssl
from paho.mqtt import client as mqtt_client

from virtualMQTTClient import VirtualMQTTclient


class MQTTClient(VirtualMQTTclient):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, brokerINC, portINC, client_idINC, ca_certs, certfile, keyfile, on_message_handler=None, topicINC = None):
        if hasattr(self, "startLoop"):
            return
        self.broker_address = brokerINC
        self.port = portINC
        self.topic = topicINC
        self.client_id = client_idINC
        self.MQTTClientLib = mqtt_client.Client(client_id=self.client_id,
                                                protocol=mqtt_client.MQTTv5)
        self.connected = False
        self.startLoop = False

        self.MQTTClientLib.on_connect = self._on_connect_callback
        self.MQTTClientLib.on_disconnect = self._on_disconnect_callback

        # Assign a custom message handler or use the default one
        if on_message_handler:
            self.MQTTClientLib.on_message = on_message_handler
        else:
            self.MQTTClientLib.on_message = self._on_message_callback
        # mTLS certificate paths
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile


    def _on_connect_callback(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client connects to the broker."""
        if reason_code == 0:
            self.connected = True
            print(f"Subscriber client '{self.client_id}' connected successfully to the broker!")
        else:
            self.connected = False
            print(f"Subscriber client '{self.client_id}' failed to connect, reason code: {reason_code}")

    def _on_disconnect_callback(self, client, userdata, rc, properties=None):
        self.connected = False
        print(f"DISCONNECTED: rc={rc}")

    def connectToBroker(self):
        """Configures TLS settings and connects to the broker."""
        if self.connected:
            return True
        if not self.connected:
            if self.ca_certs and self.certfile and self.keyfile:
                # Set up the mTLS connection
                self.MQTTClientLib.tls_set(
                    ca_certs=self.ca_certs,
                    certfile=self.certfile,
                    keyfile=self.keyfile,
                    cert_reqs=ssl.CERT_REQUIRED, # Require peer certificate verification
                    tls_version=ssl.PROTOCOL_TLS_CLIENT
                )
                self.connected = True
                print("Succesfully connected the broker")
            else:
                print("ERROR: Couldnt connect to the broker")
                return False
            
            self.MQTTClientLib.connect(self.broker_address, self.port, 60)
            self.MQTTClientLib.reconnect_delay_set(min_delay=1, max_delay=120)



    def sendToBroker(self):
        pass

    def receiveFromBroker(self):
        pass


    def subscribe_to_topic(self, topic, qos=1):
        """Subscribes the client to a specified topic with QoS."""
        result = self.MQTTClientLib.subscribe(topic, qos=qos)

        status = result[0]

        if status == 0:
            print(f"Subscribed to '{topic}' with QoS {qos}")
        else:
            print(f"Failed to subscribe to '{topic}'")

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

    def send_message(self, topic, payload, qos=1, retain=False):
        """Publishes a message to a given topic with QoS support."""
        result = self.MQTTClientLib.publish(topic, payload, qos=qos, retain=retain)

        status = result[0]

        if status == 0:
            print(f"Message sent to topic '{topic}' with QoS {qos}: {payload}")
        else:
            print(f"Failed to send message to topic '{topic}'")

    def SetMessageHandler(self,on_message_handler):
        self.MQTTClientLib.on_message = on_message_handler
