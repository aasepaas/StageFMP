from os import DirEntry
from pickle import LONG, TRUE
from PIL.Image import item
import customtkinter
from AppMap.AppWidgets.AppScrolFrameRobots import AppScrolFrameRobots
from AppMap.AppWidgets.Robot import Robot



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

    def parse_message(self, decodedMessage, topic):
        """parses the incoming MQTT messages and checks if they are valid, if so updates the robot values and returns if a new marker needs to be placed.""" 
        splitTopic = topic.split(self.topicSplit)
        markerToBePlaced = None
        #make a new robot if its not in the current list
        if not(splitTopic[1] in self.robotsDict):
            self._add_robot(splitTopic[1])

        markerToBePlaced =self._update_robot_value(name= splitTopic[1], valueField=splitTopic[2], value=decodedMessage)
        print("marker to be placed in parsed message = ", markerToBePlaced)
        print("returingning after parse message")
        return markerToBePlaced
        

    def _add_robot(self, robotName):
        """adds a robot to the robot list and the scroll frame."""
        self.robotsDict[robotName] = Robot(robotName)
        self.scrolFrame.add_new_robot_to_frame(robotName=robotName)
        self.scrolFrame.update_robot_frame(robotName, "status","online")

    
    def _update_robot_value(self, name, valueField, value):
        """updates the robot values and checks if a new marker needs to be placed, if so returns the marker info."""
        newMarker = []
        # robot positions need to be checked and if valid changed 
        if (valueField == "Position"):
            ###check if the positions message is valid
            checkedPositions = self._position_check(value)
            if checkedPositions:
                #check if new positions are the same as old positions, if not set new values
                print("comparing previous coords old = ",  self.robotsDict[name].get_current_position())
                print("new positions to check = ", checkedPositions)
                if not(checkedPositions == self.robotsDict[name].get_current_position()):
                    self.robotsDict[name].set_current_position(checkedPositions)
                    ##return that a new marker needs to be placed
                    newMarker = [name, checkedPositions[0], checkedPositions[1], checkedPositions[2] ]
                    return newMarker
        #pdate robot status 
        elif (valueField == "Status"):
            self._rarse_status_messagee(name, value)
           
        
        return newMarker

    def _position_check(self, position):
        """checks if the position message is valid(lat,lon,direction), if so returns the position info."""
        latAndLongDirection = position.split(self.msgSplit)
        print(f"{latAndLongDirection}" + f"{len(latAndLongDirection)}")
        ### latitude, longitude and direction of NESW 
        if len(latAndLongDirection) == 3:

            ###check the lat, long and direction if they are valid 
            latitude = self._is_fLoat(latAndLongDirection[0])
            longitude = self._is_fLoat(latAndLongDirection[1])
            direction = self._is_direction(self._is_fLoat(latAndLongDirection[2]))
            print(f"{latitude}" + f"{longitude}" + f"{direction}")
            ### return the lat, long and dir if valid
            if latitude and longitude and direction:
                print("position check valid")
                return [latitude, longitude, direction] 
        return False

    def _is_fLoat(self, value):
        """checks if the value can be converted to a float, if so returns the float value."""
        try:
            return float(value)
        except Exception as e:
            print("EXCEPTION: ", e)
            return False

    def _is_direction(self, direction):
        """checks if the direction is a valid direction between 0 and 360, if so returns the direction value."""
        if(direction >= 0 and direction <=360):
            return direction
        return False

    def _rarse_status_messagee(self, name, value):
        """parses the status message and updates the robot status, if the status is error, offline, done, online or driving updates the scroll frame."""
        self.robotsDict[name].set_status(value)
        if value == "error":
            self.scrolFrame.update_robot_frame(name, "status",value)
            return "error"
        elif value == "offline":
            self.scrolFrame.update_robot_frame(name, "status",value)
            return "offline"
        elif value == "done":
            self.scrolFrame.update_robot_frame(name, "status",value)
            return "done"
        elif value == "online":
            self.scrolFrame.update_robot_frame(name, "status",value)
            return "online"
        elif value == "driving":
            self.scrolFrame.update_robot_frame(name, "status",value)
            return "driving"

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




