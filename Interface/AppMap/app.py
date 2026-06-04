import copy
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


class App(customtkinter.CTk):
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

        self.MQTT_client = mqttClient
        self.app_frame_robots = AppFrameRobots(self)
        self.app_frame_robots.grid(row=0, column=0, rowspan=3, padx=(10,0), pady=(0,10), sticky="nswe")

        self.map_viewer = AppFrameMap(self, sendCallback=self.send_coordinates_to_robots, resetCallback=self.reset_interface, getRobotNames=self.app_frame_robots.get_robot_names)
        self.map_viewer.grid(row=0, column=1, rowspan=3, padx=10, pady=(0,10), sticky="nswe")




    def start_GUI(self):
        self.mainloop()

    # def GetRobotNames(self):
    #     robotNames = self.robotViewer.GetRobotNames()
    #     print("Robotnamen zijn: ", robotNames)
    
    def make_new_marker(self, markerToBePlaced):
        print("makeNewMarker van app")
        coords = [markerToBePlaced[1], markerToBePlaced[2]]
        name = markerToBePlaced[0]
        direction = markerToBePlaced[3]
        self.map_viewer.add_marker(coords=coords, direction=direction, markerText=name)

    def message_handler(self, client, userdata, msg):
        decodedMessage = msg.payload.decode()
        topic = msg.topic
        print(f"Bericht ontvangen op '{topic}': {decodedMessage}")
        markterToBePlaced = self.app_frame_robots.parse_message(decodedMessage=decodedMessage,topic=topic)
        print("marker to be placed if: " f"{markterToBePlaced}")
        if markterToBePlaced:
            print("marker to be placed is goed ")
            self.make_new_marker(markterToBePlaced)


    def send_coordinates_to_robots(self, coordsDict):
        msgField = "MoveToPosition"
        robotNames = self.app_frame_robots.get_robot_names()
        robotsToSendTo = [key for key in robotNames if key not in coordsDict]
        coords = [val for key, val in coordsDict.items() if val != None]

        print("robotstosendto: ", robotsToSendTo)
        print("coords zjin: ", coords)
        indexRange = len(robotsToSendTo) if len(robotsToSendTo) < len(coords) else len(coords)
        try:
            if self.MQTT_client is not None:
                for index in range(indexRange):
                    self.MQTT_client.send_message(f"Commands/{robotsToSendTo[index]}/{msgField}", f"{coords[index][0]},{coords[index][1]}")
                    print(f"Commands/{robotsToSendTo[index]}/{msgField}", f"{coords[index][0]},{coords[index][1]}")
        except Exception as e:
            print("Error bij sturen: ", e)

    def reset_interface(self):
        print("resetting screen")
        try:
            self.map_viewer.reset_frame()
            self.app_frame_robots.reset()
        except Exception as e:
            print("EXCEPTION: ", e)


