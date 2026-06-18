from abc import ABC, abstractmethod

class VirtualMQTTclient(ABC):
    @abstractmethod
    def subscribe_to_topic(self, topic, qos=1):
        pass
    def send_message(self, topic, payload, qos=1, retain=False):
        pass
