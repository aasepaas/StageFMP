

class Robot:
    def __init__(self, name):
        self.name = name
        self.currentPosition = []
        self.currentStatus = None


    def SetStatus(self, status):
        self.currentStatus = status

    def GetStatus(self):
        return self.currentStatus

    def GetCurrentPosition(self):
        return self.currentPosition

    def SetCurrentPosition(self, coords):
        self.currentPosition = coords


        




