import customtkinter
from PIL import Image
import os



class AppScrolFrameRobots(customtkinter.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        #self.grid_rowconfigure(0, weight=0)
        #self.grid_rowconfigure(1, weight=14)
        #self.grid_rowconfigure(2, weight=1)
        self.currentRow = 0
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.IMAGE_PATH = os.path.join(BASE_DIR, 'robotScreenshot.png')



    def AddNewRobotToFrame(self,robotName):
        self.control_frame = customtkinter.CTkFrame(self)
        self.my_image = customtkinter.CTkImage(light_image=Image.open(self.IMAGE_PATH),
	                                        dark_image=Image.open(self.IMAGE_PATH),
	                                        size=(75,75)) # WidthxHeight

        self.label = customtkinter.CTkLabel(self, text=robotName, image=self.my_image)
        #self.control_frame.grid(row=self.currentRow, column=0, padx=(10,10), pady=(10,10))
        self.label.grid(row=self.currentRow, column=0, padx=(10,10), pady=(10,10))
        self.currentRow += 1



