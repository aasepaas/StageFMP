from os import DirEntry
from pickle import LONG, TRUE
from PIL.Image import item
import customtkinter
from AppMap.AppWidgets.AppScrolFrameRobots import AppScrolFrameRobots
from AppMap.AppWidgets.Robot import Robot

NAMEFIELD = 1-1
VALUEFIELD = 2-1
STATUSFIELD = 3-1
LATFIELD = 3-1
LONGFIELD = 4-1
DIRECTIONFIELD = 5-1

class AppFrameRobots(customtkinter.CTkFrame):
    """Frame for controlling the list and robots."""
    def __init__(self, master):
        super().__init__(master)
        self.app = master
        #prededfined message splitters, used for parsing the topic and message of incoming MQTT messages
        self.topicSplit = '/'
        self.msgSplit = ','

        
        #make the column grids for which the widgets will sit in
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        #make the column rows for which the widgets will sit in
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Verkeerskegelrobots:",
                                            fg_color='#01a6f8', 
                                            width=100,
                                            height=20,
                                            font=('Bold', 28),
                                            corner_radius=5)
        self.label.grid(row=0, column=0, sticky="nw", padx=(8,8), pady=(5,5))

        self.scrolFrame = AppScrolFrameRobots(self)
        self.scrolFrame.grid(row=1, column=0,sticky="nswe", padx=(8,8), pady=(5,5))

        # dict with name, Robot object
        self.robotsDict = {}
        self.update_values = ["error", "offline", "done", "online", "driving"]
        self.update_position = "Position"

    def update_robot_status(self, message):
        """updates the robot status in the scroll frame, message is a list with the name of the robot, valuefield and the new status."""
        if not message[NAMEFIELD] in self.robotsDict:
            self._add_robot(message[NAMEFIELD])
        self._update_values(message)
        

    def _add_robot(self, robotName):
        """adds a robot to the robot list and the scroll frame."""
        self.robotsDict[robotName] = Robot(robotName)
        self.scrolFrame.add_new_robot_to_frame(robotName=robotName)
        #self.scrolFrame.update_robot_frame(robotName, "status","online")


    def _update_values(self, message):
        """parses the status message and updates the robot status, if the status is error, offline, done, online or driving updates the scroll frame."""
        name = message[NAMEFIELD]
        value_field = message[VALUEFIELD]
        print("valid status value: ", message)
        if value_field in self.update_values:
            self.robotsDict[name].set_status(message[STATUSFIELD])
            self.scrolFrame.update_robot_frame(name, "status",message[STATUSFIELD])
        elif value_field in self.update_position:
            checkedPositions = [message[LATFIELD], message[LONGFIELD], message[DIRECTIONFIELD]]
            if not(checkedPositions == self.robotsDict[name].get_current_position()):
                self.robotsDict[name].set_current_position(checkedPositions)

    def get_robot_names(self):
        """returns the robot names in the current robot list."""
        robotNames = [key for key, val in self.robotsDict.items()]
        print(robotNames)
        return robotNames 

    def reset(self):
        """resets the robot list and the scroll frame."""
        keyList = [k for k,v in self.robotsDict.items()]
        for k in keyList:
            del self.robotsDict[k]
        self.scrolFrame.ResetList()




