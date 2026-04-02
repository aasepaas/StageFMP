from abc import ABC, abstractmethod

class VirtualMQTTclient(ABC):
    @abstractmethod
    def connectToBroker(self):
        pass

    def sendToBroker(self):
        pass

    def receiveFromBroker(self):
        pass
