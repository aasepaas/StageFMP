import unittest
from unittest.mock import MagicMock, patch, call
import ssl
from MQTTClient import MQTTClient

import unittest
from unittest.mock import MagicMock, patch, mock_open, call
import ssl

from datetime import datetime, timedelta
from MQTTClient import MQTTClient

from unittest.mock import patch
from io import BytesIO
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta


class TestMQTTClient(unittest.TestCase):
    """Test MQTTClient class."""
    
    def test_singleton_instance(self):
        c1 = MQTTClient("broker", 1883, "id1", None, None, None)
        c2 = MQTTClient("broker", 1883, "id2", None, None, None)

        assert c1 is c2
        assert c1.client_id == "id1"  # init maar 1x uitgevoerd

    def test_init_only_runs_once(self):
        client = MQTTClient("broker", 1883, "id1", None, None, None)

        first_flag = client.startLoop

        # probeer opnieuw te initialiseren
        client.__init__("broker2", 1883, "id2", None, None, None)

        assert client.broker_address == "broker"
        assert client.client_id == "id1"
        assert client.startLoop == first_flag

    def test_subscribe_to_topic(self):
        client = MQTTClient("broker", 1883, "id1", None, None, None)

        client.MQTTClientLib = MagicMock()
        client.MQTTClientLib.subscribe.return_value = (0, 123)

        client.subscribe_to_topic("test/topic", qos=1)

        assert client.subscriptions[123] == "test/topic"
        client.MQTTClientLib.subscribe.assert_called_with("test/topic", qos=1)

    def test_send_message_success(self):
        client = MQTTClient("broker", 1883, "id1", None, None, None)

        client.MQTTClientLib = MagicMock()
        client.MQTTClientLib.publish.return_value = (0, 42)

        client.send_message("topic/x", "hello", qos=1)

        client.MQTTClientLib.publish.assert_called_with(
            "topic/x", "hello", qos=1, retain=False
        )


    def create_fake_crl():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"test"),
        ]))
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"test"),
        ]))
        builder = builder.public_key(key.public_key())
        builder = builder.serial_number(1234)
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=1))

        cert = builder.sign(key, hashes.SHA256())

        return cert


    def test_check_cert_not_revoked(self):
        client = MQTTClient("broker", 1883, "id1", None, None, None)

        cert = MagicMock()
        cert.serial_number = 999

        fake_crl = MagicMock()
        fake_crl.get_revoked_certificate_by_serial_number.return_value = None

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = b"fake-crl"

            with patch("MQTTClient.load_der_x509_crl") as mock_crl_loader:
                fake_crl = MagicMock()
                fake_crl.get_revoked_certificate_by_serial_number.return_value = None
                mock_crl_loader.return_value = fake_crl

                result = client._check_cert_revoked(cert, crl_url="http://fake")

        assert result is True

    def test_check_cert_revoked(self):
        client = MQTTClient("broker", 1883, "id1", None, None, None)

        cert = MagicMock()
        cert.serial_number = 1234

        fake_crl = MagicMock()
        fake_crl.get_revoked_certificate_by_serial_number.return_value = True

        result = None

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = b"fake-crl"

            with patch("MQTTClient.load_der_x509_crl") as mock_crl_loader:
                fake_crl = MagicMock()
                fake_crl.get_revoked_certificate_by_serial_number.return_value = True
                mock_crl_loader.return_value = fake_crl

                result = client._check_cert_revoked(cert, crl_url="http://fake")
                print("RESULT ========", result)

        print("RESULT ========", result)
        assert result is False






if __name__ == '__main__':
    unittest.main()
