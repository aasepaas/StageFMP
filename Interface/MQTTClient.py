import random
import ssl
from paho.mqtt import client as mqtt_client
import ssl
import urllib.request
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cryptography.x509 import load_der_x509_crl
import socket
from virtualMQTTClient import VirtualMQTTclient


class MQTTClient(VirtualMQTTclient):
    """Implements a singleton MQTT client for connecting, subscribing, and publishing messages to an MQTT broker with mTLS support."""
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
        self.MQTTClientLib.on_subscribe = self._on_subscribe_callback

        # Assign a custom message handler or use the default one
        if on_message_handler:
            self.MQTTClientLib.on_message = on_message_handler
        else:
            self.MQTTClientLib.on_message = self._on_message_callback
        # mTLS certificate paths
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile
        self.subscriptions = {}


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

    def _on_subscribe_callback(self, client, userdata, mid, reason_code, properties=None):
        """Callback for when the client subscribes to a topic, to determine the status of subscription"""

        topic = self.subscriptions.get(mid, "UNKNOWN TOPIC")

        if "Granted" in str(reason_code):
            print(f"Subscription to '{topic}' was successful")
        else:
            print(f"WARNING: Subscription to '{topic}' failed (reason_code={reason_code})")

    def connectToBroker(self, crl_url=None):
        """Configures TLS settings and connects to the broker."""
        if self.connected:
            return True
        
        #first get broker certificate 
        print("get broker cert")
        try:
            broker_cert = self._get_broker_cert()
        except Exception as e:
            print(f"Error retrieving broker certificate: {e}")
            return False
        #check if broker certificate is revoked using CRL
        try:
            if not self._check_cert_revoked(broker_cert, crl_url=crl_url):
                print("Broker certificate is revoked. Aborting connection.")
                return False
        except Exception as e:
            print(f"Error checking certificate revocation: {e}")
            return False
        #if broker cert valid try to make a mTLS connection to the broker
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
            else:
                print("ERROR: Couldnt connect to the broker")
                return False
            
            self.MQTTClientLib.reconnect_delay_set(min_delay=1, max_delay=120)
            self.MQTTClientLib.connect(self.broker_address, self.port, 60)

            self.listen_for_messages()




    def sendToBroker(self):
        pass

    def receiveFromBroker(self):
        pass


    def subscribe_to_topic(self, topic, qos=1):
        """Subscribes the client to a specified topic with QoS."""
        result = self.MQTTClientLib.subscribe(topic, qos=qos)

        status = result[0]
        mid = result[1]

        if status == 0:
            self.subscriptions[mid] = topic
            print(f"Subscribed to '{topic}' with QoS {qos}")
        else:
            print(f"Failed to subscribe to '{topic}'")

    def _on_message_callback(self, MQTTClientLib, userdata, msg):
        """The default callback for receiving messages."""
        print(f"Subscriber client '{self.client_id}' received message from topic '{msg.topic}': {msg.payload.decode()}")

    def listen_for_messages(self):
        """Starts a threaded loop to listen for incoming messages."""
        """This is non-blocking!!"""
        if not self.startLoop:
            self.MQTTClientLib.loop_start()
            self.startLoop = True

    def disconnect_client(self):
        """Disconnects the client from the broker."""
        if self.connected:
            self.MQTTClientLib.disconnect()
            self.connected = False

    def get_connection_status(self):
        return self.connected

    def _get_broker_cert(self):
        """Retrieves the broker's certificate for revocation checking."""
        # Create an SSL context to connect to the broker and retrieve its certificate
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=self.ca_certs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Connect to the broker and retrieve the certificate in DER format
        with socket.create_connection((self.broker_address, self.port), timeout=10) as sock:
            with context.wrap_socket(sock) as ssock:
                raw_cert = ssock.getpeercert(binary_form=True)

        return x509.load_der_x509_certificate(raw_cert, default_backend())
    
    def _check_cert_revoked(self, cert, crl_url=None):
        """Checks if the given certificate is revoked using the CRL at the specified URL."""
        #if crl not included in cert, try to get it from the CRL distribution points extension
        if not crl_url:
            try:
                cdp = cert.extensions.get_extension_for_class(x509.CRLDistributionPoints)
                for dp in cdp.value:
                    for name in dp.full_name:
                            crl_url = name.value
                            break
            except Exception as e:
                print(f"Error retrieving CRL distribution points: {e}")
                return False
        #check if we have a CRL URL to check against    
        print(f"Checking CRL at: {crl_url}")
        with urllib.request.urlopen(crl_url, timeout=10) as response:
            crl_data = response.read()
        # Determine if the CRL is in PEM or DER format and load it accordingly
        if crl_data.startswith(b"-----BEGIN"):
            crl = x509.load_pem_x509_crl(crl_data, default_backend())
        else:
            crl = load_der_x509_crl(crl_data, default_backend())
        #check if broker serial number is revoked by comparing it to the serial numbers in the CRL
        serial = cert.serial_number
        revoked = crl.get_revoked_certificate_by_serial_number(serial)
        if revoked:
            print(f"Certificate with serial {serial} is revoked.")
            return False
        else:
            print(f"Certificate with serial {serial} is not revoked.")
            return True
        

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