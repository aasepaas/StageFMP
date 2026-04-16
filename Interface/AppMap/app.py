from customtkinter.windows.widgets import appearance_mode
import customtkinter

from virtualMQTTClient import VirtualMQTTclient


from .AppWidgets import *
#from . import AppFrame
#from tkinter.tix import COLUMN

WIDTH = 1280
HEIGHT = 720
MAXWIDTH = 1920
MAXHEIGHT = 1080
APPNAME = "Kegelrobots besturingsapp"


class app(customtkinter.CTk):
    _instance = None
    ##singleton zodat er niet perongeluk meerdere interfaces gemaakt kunnen worden
    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
        return cls._instance
    #init van de klasse tijdens aanmaken van object
    def __init__(self, mqttClient):
        #check of er een attribuut is aangemaakt, zo niet maak een nieuw object aan, zo wel object bestaat al
        if "init" in self.__dict__:
            return
        ###globale init van app met naam, grootte en gridstijl
        super().__init__()
        self.title(APPNAME)
        self.init = True

        self.geometry(str(WIDTH) + "x" + str(HEIGHT))    
        self.minsize(WIDTH, HEIGHT)
        self.maxsize(MAXWIDTH, MAXHEIGHT)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)
        self.grid_rowconfigure(2, weight=1)

        self.var = customtkinter.BooleanVar()

        self.MQTTClient = mqttClient

        self.mapViewer = AppFrameMap(self, sendCallback=self.SendCoordinatesToRobots)
        self.mapViewer.grid(row=0, column=1, rowspan=3, padx=10, pady=(0,10), sticky="nswe")
        self.robotViewer = AppFrameRobots(self)
        self.robotViewer.grid(row=0, column=0, rowspan=3, padx=(10,0), pady=(0,10), sticky="nswe")



    def startGUI(self):
        self.mainloop()

    def makeNewMarker(self, markerToBePlaced):
        print("makeNewMarker van app")
        coords = [markerToBePlaced[1], markerToBePlaced[2]]
        name = markerToBePlaced[0]
        direction = markerToBePlaced[3]
        self.mapViewer.AddMarker(coords=coords, direction=direction, markerText=name)

    def MessageHandler(self, client, userdata, msg):
        decodedMessage = msg.payload.decode()
        topic = msg.topic
        print(f"Bericht ontvangen op '{topic}': {decodedMessage}")
        markterToBePlaced = self.robotViewer.parseMessage(decodedMessage=decodedMessage,topic=topic)
        print("marker to be placed if: " f"{markterToBePlaced}")
        if markterToBePlaced:
            print("marker to be placed is goed ")
            self.makeNewMarker(markterToBePlaced)


    def SendCoordinatesToRobots(self, coordsList):
        msgField = "MoveToPosition"
        robotNames = self.robotViewer.GetRobotNames()
        robotsToSendTo = [key for key, val in coordsList.items() if val not in robotNames]
        coords = [val for key, val in coordsList.items()]
        if len(coords) >= len(robotsToSendTo):
            if self.MQTTClient is not None:
                for index in range(len(coords)):
                    self.MQTTClient.send_message(f"Commands/{robotNames[index]}/{msgField}", f"{coords[index][0]},{coords[index][1]}")
                    print(f"Robots/{robotNames[index]}/{msgField}", f"{coords[index][0]},{coords[index][1]}")
