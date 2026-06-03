from os import DirEntry
from pickle import LONG, TRUE
from PIL.Image import item
import customtkinter
from AppMap.AppWidgets.AppScrolFrameRobots import AppScrolFrameRobots
from AppMap.AppWidgets.Robot import Robot



class AppFrameRobots(customtkinter.CTkFrame):
    """Frame for controlling the list and robots"""
    def __init__(self, master):
        super().__init__(master)
        self.app = master
        ###prededfined message splitters
        self.topicSplit = '/'
        self.msgSplit = ','

        
        ###make the column grids for which the widgets will sit in
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ###make the column rows for which the widgets will sit in
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

        ### dict with name, Robot object
        self.robotsDict = {}

    def parseMessage(self, decodedMessage, topic):
        splitTopic = topic.split(self.topicSplit)
        markerToBePlaced = None
        ###make a new robot if its not in the current list
        if not(splitTopic[1] in self.robotsDict):
            self.addRobot(splitTopic[1])

        markerToBePlaced =self.updateRobotValue(name= splitTopic[1], valueField=splitTopic[2], value=decodedMessage)
        print("marker to be placed in parsed message = ", markerToBePlaced)
        print("returingning after parse message")
        return markerToBePlaced
        

    def addRobot(self, robotName):
        self.robotsDict[robotName] = Robot(robotName)
        self.scrolFrame.AddNewRobotToFrame(robotName=robotName)
        self.scrolFrame.UpdateRobotFrame(robotName, "status","online")

                 
    def deleteRobot(self, robotName):
        pass
        
    
    def updateRobotValue(self, name, valueField, value):
        newMarker = []
        ### robot positions need to be checked and if valid changed 
        if (valueField == "Position"):
            ###check if the positions message is valid
            checkedPositions = self.PositionCheck(value)
            if checkedPositions:
                ###check if new positions are the same as old positions, if not set new values
                print("comparing previous coords old = ",  self.robotsDict[name].GetCurrentPosition())
                print("new positions to check = ", checkedPositions)
                if not(checkedPositions == self.robotsDict[name].GetCurrentPosition()):
                    self.robotsDict[name].SetCurrentPosition(checkedPositions)
                    ###return that a new marker needs to be placed
                    newMarker = [name, checkedPositions[0], checkedPositions[1], checkedPositions[2] ]
                    return newMarker
        ###update robot status 
        elif (valueField == "Status"):
            self.ParseStatusMessage(name, value)
           
        
        return newMarker

    def PositionCheck(self, position):
        latAndLongDirection = position.split(self.msgSplit)
        print(f"{latAndLongDirection}" + f"{len(latAndLongDirection)}")
        ### latitude, longitude and direction of NESW 
        if len(latAndLongDirection) == 3:

            ###check the lat, long and direction if they are valid 
            latitude = self.IsFLoat(latAndLongDirection[0])
            longitude = self.IsFLoat(latAndLongDirection[1])
            direction = self.IsDirection(self.IsFLoat(latAndLongDirection[2]))
            print(f"{latitude}" + f"{longitude}" + f"{direction}")
            ### return the lat, long and dir if valid
            if latitude and longitude and direction:
                print("position check valid")
                return [latitude, longitude, direction] 
        return False

    def IsFLoat(self, value):
        try:
            return float(value)
        except Exception as e:
            print("EXCEPTION: ", e)
            return False

    def IsDirection(self, direction):
        if(direction >= 0 and direction <=360):
            return direction
        return False

    def ParseStatusMessage(self, name, value):
        self.robotsDict[name].SetStatus(value)
        if value == "error":
            self.scrolFrame.UpdateRobotFrame(name, "status",value)
            return "error"
        elif value == "offline":
            self.scrolFrame.UpdateRobotFrame(name, "status",value)
            return "offline"
        elif value == "done":
            self.scrolFrame.UpdateRobotFrame(name, "status",value)
            return "done"
        elif value == "online":
            self.scrolFrame.UpdateRobotFrame(name, "status",value)
            return "online"
        elif value == "driving":
            self.scrolFrame.UpdateRobotFrame(name, "status",value)
            return "driving"

    def GetRobotNames(self):
        robotNames = [key for key, val in self.robotsDict.items()]
        print(robotNames)
        return robotNames 

    def Reset(self):
        keyList = [k for k,v in self.robotsDict.items()]
        for k in keyList:
            del self.robotsDict[k]
        self.scrolFrame.ResetList()




