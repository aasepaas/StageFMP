import customtkinter
from AppMap.AppWidgets.AppScrolFrameRobots import AppScrolFrameRobots


class AppFrameRobots(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ###make the column grids for which the widgets will sit in
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ###make the column rows for which the widgets will sit in
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Robot list:",
                                            fg_color='#01a6f8', 
                                            width=100,
                                            height=20,
                                            font=('Bold', 28),
                                            corner_radius=5)
        self.label.grid(row=0, column=0, sticky="nw", padx=(8,8), pady=(5,5))

        self.scrolFrame = AppScrolFrameRobots(self)
        self.scrolFrame.grid(row=1, column=0,sticky="nswe", padx=(8,8), pady=(5,5))



