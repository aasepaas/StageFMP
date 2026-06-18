import copy
from AppMap.TextInterpreter import InputInterpreter
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
NAMEFIELD = 1 -1
VALUEFIELD = 2 -1
STATUSFIELD = 3-1
LATFIELD = 3-1
LONGFIELD = 4-1
DIRECTIONFIELD = 5-1


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

        #self.map_viewer = AppFrameMap(self, sendCallback=self._send_coordinates_to_robots, resetCallback=self.reset_interface, getRobotNames=self.app_frame_robots.get_robot_names)

        self.map_viewer = AppFrameMap(self,send_callback=self._send_coordinates_to_robots,
                                      reset_callback=self.reset_interface,
                                      get_robot_names_callback=self.app_frame_robots.get_robot_names,
                                      general_callback=self.callback_handler)

            
        self.map_viewer.grid(row=0, column=1, rowspan=3, padx=10, pady=(0,10), sticky="nswe")
        self.input_interpreter = InputInterpreter(self.callback_handler)


    def callback_handler(self, callback, *args, **kwargs):
        """Handles callbacks from child widgets."""
        if callback == "send_coordinates":
            self._send_coordinates_to_robots(*args, **kwargs)
        elif callback == "reset_interface":
            self.reset_interface()
        elif callback == "get_robot_names":
            return self.app_frame_robots.get_robot_names()
        elif callback == "home_robots":
            self._home_robots()
           



    def start_GUI(self):
        self.mainloop()
    
    def make_new_marker(self, markerToBePlaced):
        ###markerToBePlaced is een lijst met de naam van de robot, valuefield, de lat, lon en de richting van de robot
        print("makeNewMarker van app, MESSAGE = ", markerToBePlaced)
        #self.map_viewer.add_marker(coords=[markerToBePlaced[LATFIELD], markerToBePlaced[LONGFIELD]]
        #                           ,direction=markerToBePlaced[DIRECTIONFIELD], markerText=markerToBePlaced[NAMEFIELD])
        self.map_viewer._on_add_marker(coords=[markerToBePlaced[LATFIELD], markerToBePlaced[LONGFIELD]], name=markerToBePlaced[NAMEFIELD])
    

    def message_handler(self, client, userdata, msg):
        decodedMessage = msg.payload.decode()
        topic = msg.topic
        print(f"Bericht ontvangen op '{topic}': {decodedMessage}")
        msg_to_return = self.input_interpreter.parse_message(decodedMessage=decodedMessage,topic=topic)
        print("message to be returned if: " f"{msg_to_return}")
        if msg_to_return:
            print("message to be returned is goed ")
            self._after_message_handling(msg_to_return)

    def _after_message_handling(self, msg_to_return):
        print("MESSSSSSSSSSSAGE AFTER HANDLING = ", msg_to_return)
        if  "Position" in msg_to_return:
            self.make_new_marker(msg_to_return)
            self.app_frame_robots.update_robot_status(msg_to_return)
        elif "Status" in msg_to_return:
            self.app_frame_robots.update_robot_status(msg_to_return)
        else:
            print("No valid message to process after handling.") 

    def _send_coordinates_to_robots(self, coordsDict):
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
            print("Error bij sturen posities: ", e)

    def _home_robots(self):
        robotNames = self.app_frame_robots.get_robot_names()
        msgField = "MoveToPosition"
        try:
            for index in robotNames:
                self.MQTT_client.send_message(f"Commands/{index}/{msgField}", f"home")
                print(f"Commands/{index}/{msgField}", f"home")
        except Exception as e:
            print("Error bij sturen naar home: ", e) 

    def reset_interface(self):
        print("resetting screen")
        try:
            self.map_viewer.reset_frame()
            self.app_frame_robots.reset()
        except Exception as e:
            print("EXCEPTION: ", e)


