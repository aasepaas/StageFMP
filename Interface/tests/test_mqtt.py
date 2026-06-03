import unittest
from unittest.mock import MagicMock, patch, call
import ssl
from MQTTClient import MQTTClient

import unittest
from unittest.mock import MagicMock, patch, mock_open, call
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from MQTTClient import MQTTClient, MAX_PAYLOAD


class TestMQTTClient(unittest.TestCase):
    """Test MQTTClient class."""
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Reset singleton
        MQTTClient._instance = None
        
        self.broker = "test.broker.com"
        self.port = 8883
        self.client_id = "test_client"
        self.ca_certs = "/path/to/ca.crt"
        self.certfile = "/path/to/client.crt"
        self.keyfile = "/path/to/client.key"
        self.crl_url = "http://example.com/crl.pem"
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset singleton
        MQTTClient._instance = None
    
    # ── Singleton Pattern Tests ──────────────────────────────────────────
    
    def test_singleton_same_instance(self):
        """Test that multiple instantiations return the same instance."""
        with patch('paho.mqtt.client.Client'):
            client1 = MQTTClient(self.broker, self.port, "client1", 
                               self.ca_certs, self.certfile, self.keyfile)
            client2 = MQTTClient(self.broker, self.port, "client1",
                               self.ca_certs, self.certfile, self.keyfile)
            
            self.assertIs(client1, client2)
    
    def test_singleton_prevents_reinit(self):
        """Test that singleton prevents re-initialization."""
        with patch('paho.mqtt.client.Client') as mock_mqtt_client:
            client1 = MQTTClient(self.broker, self.port, "client1",
                               self.ca_certs, self.certfile, self.keyfile)
            
            # Try to re-init with different parameters
            client2 = MQTTClient("different.broker.com", 1883, "client2",
                               self.ca_certs, self.certfile, self.keyfile)
            
            # Should have same broker address
            self.assertEqual(client1.broker_address, self.broker)
            self.assertEqual(client2.broker_address, self.broker)
    
    # ── Initialization Tests ─────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_initialization(self, mock_mqtt_client_class):
        """Test proper initialization of MQTTClient."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile,
                           topicINC="test/topic")
        
        self.assertEqual(client.broker_address, self.broker)
        self.assertEqual(client.port, self.port)
        self.assertEqual(client.client_id, self.client_id)
        self.assertEqual(client.topic, "test/topic")
        self.assertEqual(client.ca_certs, self.ca_certs)
        self.assertEqual(client.certfile, self.certfile)
        self.assertEqual(client.keyfile, self.keyfile)
        self.assertFalse(client.connected)
        self.assertFalse(client.startLoop)
    
    @patch('paho.mqtt.client.Client')
    def test_initialization_with_custom_message_handler(self, mock_mqtt_client_class):
        """Test initialization with custom message handler."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        custom_handler = MagicMock()
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile,
                           on_message_handler=custom_handler)
        
        self.assertEqual(mock_mqtt_instance.on_message, custom_handler)
    
    @patch('paho.mqtt.client.Client')
    def test_initialization_without_custom_handler(self, mock_mqtt_client_class):
        """Test initialization uses default message handler when none provided."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        # Should set default handler
        self.assertIsNotNone(mock_mqtt_instance.on_message)
    
    # ── Connection Callback Tests ────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_on_connect_callback_success(self, mock_mqtt_client_class):
        """Test on_connect_callback with successful connection (reason_code 0)."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        # Simulate successful connection
        client._on_connect_callback(None, None, None, 0, None)
        
        self.assertTrue(client.connected)
    
    @patch('paho.mqtt.client.Client')
    def test_on_connect_callback_failure(self, mock_mqtt_client_class):
        """Test on_connect_callback with failed connection."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        # Simulate failed connection
        client._on_connect_callback(None, None, None, 4, None)
        
        self.assertFalse(client.connected)
    
    # ── Disconnect Callback Tests ────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_on_disconnect_callback(self, mock_mqtt_client_class):
        """Test on_disconnect_callback sets connected to False."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        
        client._on_disconnect_callback(None, None, 0, None)
        
        self.assertFalse(client.connected)
    
    # ── Connection Tests ────────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_connectToBroker_already_connected(self, mock_mqtt_client_class):
        """Test connectToBroker returns True if already connected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        
        result = client.connectToBroker()
        
        self.assertTrue(result)
    
    @patch('paho.mqtt.client.Client')
    def test_connectToBroker_success(self, mock_mqtt_client_class):
        """Test successful connection to broker with mTLS."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        client.connectToBroker()
        
        # Verify tls_set was called with correct parameters
        mock_mqtt_instance.tls_set.assert_called_once()
        call_kwargs = mock_mqtt_instance.tls_set.call_args[1]
        self.assertEqual(call_kwargs['ca_certs'], self.ca_certs)
        self.assertEqual(call_kwargs['certfile'], self.certfile)
        self.assertEqual(call_kwargs['keyfile'], self.keyfile)
        self.assertEqual(call_kwargs['cert_reqs'], ssl.CERT_REQUIRED)
        self.assertEqual(call_kwargs['tls_version'], ssl.PROTOCOL_TLS_CLIENT)
    
    @patch('paho.mqtt.client.Client')
    def test_connectToBroker_calls_connect(self, mock_mqtt_client_class):
        """Test that connectToBroker calls connect with correct parameters."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        client.connectToBroker()
        
        # Verify connect was called
        mock_mqtt_instance.connect.assert_called_once_with(self.broker, self.port, 60)
    
    @patch('paho.mqtt.client.Client')
    def test_connectToBroker_sets_reconnect_delay(self, mock_mqtt_client_class):
        """Test that connectToBroker sets reconnect delay."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        client.connectToBroker()
        
        mock_mqtt_instance.reconnect_delay_set.assert_called_once_with(min_delay=1, max_delay=120)
    
    @patch('paho.mqtt.client.Client')
    def test_connectToBroker_missing_certificates(self, mock_mqtt_client_class):
        """Test connectToBroker returns False when certificates are missing."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           None, None, None)
        client.connected = False
        
        result = client.connectToBroker()
        
        self.assertFalse(result)
    
    # ── Subscribe Tests ─────────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_subscribe_to_topic_success(self, mock_mqtt_client_class):
        """Test successful subscription to topic."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.subscribe.return_value = (0, 1)  # (status, mid)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.subscribe_to_topic("test/topic", qos=1)
        
        mock_mqtt_instance.subscribe.assert_called_once_with("test/topic", qos=1)
    
    @patch('paho.mqtt.client.Client')
    def test_subscribe_to_topic_failure(self, mock_mqtt_client_class):
        """Test failed subscription to topic."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.subscribe.return_value = (1, 1)  # (status != 0, mid)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.subscribe_to_topic("test/topic", qos=1)
        
        mock_mqtt_instance.subscribe.assert_called_once_with("test/topic", qos=1)
    
    @patch('paho.mqtt.client.Client')
    def test_subscribe_to_topic_custom_qos(self, mock_mqtt_client_class):
        """Test subscription with custom QoS level."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.subscribe.return_value = (0, 1)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.subscribe_to_topic("test/topic", qos=2)
        
        mock_mqtt_instance.subscribe.assert_called_once_with("test/topic", qos=2)
    
    # ── Message Handler Tests ────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_on_message_callback(self, mock_mqtt_client_class):
        """Test default message callback."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        # Create mock message
        mock_msg = MagicMock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b"test payload"
        
        # Call callback (shouldn't raise exception)
        client._on_message_callback(None, None, mock_msg)
    
    @patch('paho.mqtt.client.Client')
    def test_set_message_handler(self, mock_mqtt_client_class):
        """Test setting custom message handler."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        custom_handler = MagicMock()
        client.SetMessageHandler(custom_handler)
        
        self.assertEqual(mock_mqtt_instance.on_message, custom_handler)
    
    # ── Listen Tests ────────────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_listen_for_messages_not_connected(self, mock_mqtt_client_class):
        """Test listen_for_messages when not connected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        client.listen_for_messages()
        
        mock_mqtt_instance.loop_start.assert_not_called()
    
    @patch('paho.mqtt.client.Client')
    def test_listen_for_messages_connected(self, mock_mqtt_client_class):
        """Test listen_for_messages when connected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        client.startLoop = False
        
        client.listen_for_messages()
        
        mock_mqtt_instance.loop_start.assert_called_once()
        self.assertTrue(client.startLoop)
    
    @patch('paho.mqtt.client.Client')
    def test_listen_for_messages_already_running(self, mock_mqtt_client_class):
        """Test listen_for_messages doesn't restart if already running."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        client.startLoop = True
        
        client.listen_for_messages()
        
        mock_mqtt_instance.loop_start.assert_not_called()
    
    # ── Send Message Tests ──────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_send_message_success(self, mock_mqtt_client_class):
        """Test successful message publish."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.publish.return_value = (0, 1)  # (status, mid)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.send_message("test/topic", "test payload", qos=1, retain=False)
        
        mock_mqtt_instance.publish.assert_called_once_with(
            "test/topic", "test payload", qos=1, retain=False
        )
    
    @patch('paho.mqtt.client.Client')
    def test_send_message_failure(self, mock_mqtt_client_class):
        """Test failed message publish."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.publish.return_value = (1, 0)  # (status != 0, mid)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.send_message("test/topic", "test payload")
        
        mock_mqtt_instance.publish.assert_called_once()
    
    @patch('paho.mqtt.client.Client')
    def test_send_message_with_retain(self, mock_mqtt_client_class):
        """Test send message with retain flag."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_instance.publish.return_value = (0, 1)
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        
        client.send_message("test/topic", "test payload", retain=True)
        
        mock_mqtt_instance.publish.assert_called_once_with(
            "test/topic", "test payload", qos=1, retain=True
        )
    
    # ── Disconnect Tests ────────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_disconnect_client_connected(self, mock_mqtt_client_class):
        """Test disconnecting when connected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        
        client.disconnect_client()
        
        mock_mqtt_instance.disconnect.assert_called_once()
        self.assertFalse(client.connected)
    
    @patch('paho.mqtt.client.Client')
    def test_disconnect_client_not_connected(self, mock_mqtt_client_class):
        """Test disconnecting when already disconnected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        client.disconnect_client()
        
        mock_mqtt_instance.disconnect.assert_not_called()
    
    # ── Status Tests ────────────────────────────────────────────────────
    
    @patch('paho.mqtt.client.Client')
    def test_connection_status_connected(self, mock_mqtt_client_class):
        """Test connectionStatus returns True when connected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = True
        
        self.assertTrue(client.connectionStatus())
    
    @patch('paho.mqtt.client.Client')
    def test_connection_status_disconnected(self, mock_mqtt_client_class):
        """Test connectionStatus returns False when disconnected."""
        mock_mqtt_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_mqtt_instance
        
        client = MQTTClient(self.broker, self.port, self.client_id,
                           self.ca_certs, self.certfile, self.keyfile)
        client.connected = False
        
        self.assertFalse(client.connectionStatus())

   #-----tests met crll--------------



if __name__ == '__main__':
    unittest.main()
