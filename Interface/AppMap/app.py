from customtkinter.windows.widgets import appearance_mode
import customtkinter

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
    def __init__(self):
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

        # ##variabelen die gebruikt worden door het doc heen
        # self.button = customtkinter.CTkButton(self, text="my button", command=self.button_callback)
        # self.button.grid(row=0, column=0,columnspan=2, padx=10, pady=10, sticky="ew")
        self.var = customtkinter.BooleanVar()
        
        
        # self.checkboxFrame1 = AppFrame(self, values=["box1", "box3", "box4"], masterCallbackFunction = self.checkbox_callback)
        # self.checkboxFrame2 = AppFrame(self, values=["box1", "box3", "box4"], masterCallbackFunction = self.checkbox_callback)

        # self.checkboxFrame1.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        # self.checkboxFrame2.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="wnes")
        self.mapViewer = AppFrameMap(self)
        self.mapViewer.grid(row=0, column=1, rowspan=3, padx=10, pady=(0,10), sticky="nswe")
        self.robotViewer = AppFrameRobots(self)
        self.robotViewer.grid(row=0, column=0, rowspan=3, padx=(10,0), pady=(0,10), sticky="nswe")




        
    def button_callback(self):
        print("button pressed")

    def checkbox_callback(self):
        print(self.checkboxFrame1.get())
        print(self.checkboxFrame2.get())

    def startGUI(self):
        self.mainloop()

    def handleMessages():
        pass
