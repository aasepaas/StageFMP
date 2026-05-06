class customLogger():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if hasattr(self, "initialised"):
            return

        self.initialised = True
        self.Waarde = None

    def prRed(self,s): print("\033[91m {}\033[00m".format(s))
    def prGreen(self,s): print("\033[92m {}\033[00m".format(s))
    def prYellow(self,s): print("\033[93m {}\033[00m".format(s))
    def prLightPurple(self,s): print("\033[94m {}\033[00m".format(s))
    def prPurple(self,s): print("\033[95m {}\033[00m".format(s))
    def prCyan(self,s): print("\033[96m {}\033[00m".format(s))
    def prLightGray(self,s): print("\033[97m {}\033[00m".format(s))
    def prBlack(self,s): print("\033[90m {}\033[00m".format(s))  

    def setWaarde(self, waarde):
        self.Waarde = waarde

    def getWaarde(self):
        return self.Waarde


            
