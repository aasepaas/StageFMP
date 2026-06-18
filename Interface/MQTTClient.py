import random
import ssl
from xml.etree.ElementTree import tostring
from paho.mqtt import client as mqtt_client

from virtualMQTTClient import VirtualMQTTclient

from customLogger import customLogger
import urllib.request

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cryptography.x509 import load_der_x509_crl, load_pem_x509_certificate
from cryptography.hazmat.primitives.serialization import Encoding
from time import sleep
import datetime


MAX_PAYLOAD = 950

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
        self.MQTTClientLib.on_subscribe = self.on_subscribe

        # Assign a custom message handler or use the default one
        if on_message_handler:
            self.MQTTClientLib.on_message = on_message_handler
        else:
            self.MQTTClientLib.on_message = self._on_message_callback
        # mTLS certificate paths
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile
        self.topics_connected_to = {}
        self.current_topic_num = 1
        self.subscriped_mids = []



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
        if properties:
            print(properties)

 

    def sendToBroker(self):
        pass

    def receiveFromBroker(self):
        pass


    def subscribe_to_topic(self, topic, qos=1):
        """Subscribes the client to a specified topic with QoS."""
        result = self.MQTTClientLib.subscribe(topic, qos=qos)

        sleep(0.1)
        print("result van sub: ", result)

        status = result[1]
        print("STTUAS", status)
        self.current_topic_num += 1
   
        self.topics_connected_to[status] = topic
        #status = result[0]

        # if status == 0:
        #     print(f"Subscribed to '{topic}' with QoS {qos}")
        # else:
        #     print(f"Failed to subscribe to '{topic}'")

    def _on_message_callback(self, MQTTClientLib, userdata, msg):
        """The default callback for receiving messages."""
        print(f"Subscriber client '{self.client_id}' received message from topic '{msg.topic}': {msg.payload.decode()}")


    def get_subscriptions(self):
        succesful_topics = [val for key, val in self.topics_connected_to.items() if key in self.subscriped_mids]
        print("succesfulle connected to: ", succesful_topics)

    def on_subscribe(self, client, userdata, mid, reasoncodes, properties):
        print("suback:")
        print("reasoncodes:", reasoncodes)
        print("userdata: ", userdata)
        print("client", client)
        print(reasoncodes[0])
        check_value = reasoncodes[0].is_failure
        if not check_value:
            #print("\nsuccesfully connected to topic: ", self.topics_connected_to[mid])
            self.subscriped_mids.append(float(mid))
        print(f"topic reasoncodes",reasoncodes)


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

    def connectionStatus(self):
        return self.connected

    def send_message(self, topic, payload, qos=1, retain=False):
        """Publishes a message to a given topic with QoS support."""

        payload_size = len(payload.encode("utf-8"))

        if payload_size > MAX_PAYLOAD:
            print(f"Payload too large: {payload_size} bytes")
            return False

        self.MQTTClientLib.publish(topic, payload, qos=qos, retain=retain)

    def SetMessageHandler(self,on_message_handler):
        self.MQTTClientLib.on_message = on_message_handler


    def _get_broker_cert(self) -> x509.Certificate:
        """Haal het broker-certificaat op via een tijdelijke SSL-verbinding."""
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=self.ca_certs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Alleen ophalen, nog niet verifiëren

        import socket
        with socket.create_connection((self.broker_address, self.port), timeout=10) as sock:
            with context.wrap_socket(sock) as ssock:
                raw_cert = ssock.getpeercert(binary_form=True)

        return x509.load_der_x509_certificate(raw_cert, default_backend())

    def _check_cert_revoked(self, cert: x509.Certificate, crl_url: str | None = None) -> bool:
        """
        Controleer of een certificaat ingetrokken is via de CRL.
        Geeft True terug als GELDIG, False als INGETROKKEN.
        """
        # Haal CRL URL uit het certificaat zelf als niet meegegeven
        if not crl_url:
            try:
                cdp = cert.extensions.get_extension_for_class(x509.CRLDistributionPoints)
                for dp in cdp.value:
                    for name in dp.full_name:
                        crl_url = name.value
                        break
            except x509.ExtensionNotFound:
                pass

        if not crl_url:
            print("Geen CRL URL gevonden, check overgeslagen.")
            return True

        print(f"CRL ophalen van: {crl_url}")
        with urllib.request.urlopen(crl_url, timeout=10) as response:
            crl_data = response.read()

        # DER of PEM detecteren
        if crl_data.startswith(b"-----BEGIN"):
            crl = x509.load_pem_x509_crl(crl_data, default_backend())
        else:
            crl = load_der_x509_crl(crl_data, default_backend())

        serial = cert.serial_number
        revoked = crl.get_revoked_certificate_by_serial_number(serial)

        if revoked:
            print(f"GEBLOKKEERD: Serienummer {serial} ingetrokken!")
            return False

        print(f"OK: Serienummer {serial} is geldig.")
        return True

    def connectToBroker(self, crl_url: str | None = None):
        if self.connected:
            return True

        if not (self.ca_certs and self.certfile and self.keyfile):
            print("ERROR: Certificaatbestanden ontbreken.")
            return False

        # 1. Haal broker-certificaat op
        print("Broker-certificaat ophalen voor CRL-check...")
        try:
            broker_cert = self._get_broker_cert()
            print(f"Broker cert subject: {broker_cert.subject}")
        except Exception as e:
            print(f"FOUT: Kon broker-certificaat niet ophalen: {e}")
            return False

        # 2. Check of broker-cert ingetrokken is
        try:
            if not self._check_cert_revoked(broker_cert, crl_url):
                print("Verbinding geweigerd: broker-certificaat is ingetrokken.")
                return False
        except:
            print("Verbinding geweigerd geen succesvolle CRL kunnen ophalen")
            return True

        # 3. Echte mTLS verbinding opzetten
        self.MQTTClientLib.tls_set(
            ca_certs=self.ca_certs,
            certfile=self.certfile,
            keyfile=self.keyfile,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT
        )

        self.MQTTClientLib.enable_logger()
        self.MQTTClientLib.reconnect_delay_set(min_delay=1, max_delay=120)
        self.MQTTClientLib.connect(self.broker_address, self.port, 60)

        self.listen_for_messages()
        # self.connected = True
        # print("Succesvol verbonden met de broker.")
        return True