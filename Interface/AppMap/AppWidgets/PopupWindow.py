import customtkinter
from AppMap.AppWidgets.FormationParser import parse_input


class PopupWindow(customtkinter.CTkToplevel):
    def __init__(self, master, callbackValues):
        self.master = master
        self.afterPopupCallback = callbackValues

    def pop_up(self, listOfRobotNames=["robot1", "robot2"]):

        chosenSettings = {"Aantal": None, "Formatie": None, "RobotStart": None}

        def klaarKnopCommand():
            text = textbox.get("0.0", "end")
            print(text)
            try:
                parsedInput = parse_input(text)
                print(parsedInput)
            except Exception as e:
                print("Exception! parsing niet goed: ", e)
            if any(val is None for val in chosenSettings.values()):
                print("selecteer alle waardes voor returneren")
                return
            popup.destroy()
            self.afterPopupCallback(chosenSettings)

        def change_val(value):
            try:
                int(value)
                chosenSettings["Aantal"] = value
            except Exception:
                pass

        def changeFormation(formation):
            chosenSettings["Formatie"] = formation

        def changeStartRobot(robotName):
            chosenSettings["RobotStart"] = robotName

        popup = customtkinter.CTkToplevel(self.master)
        popup.title("Instellingen voor berekeningen")
        popup.wm_maxsize(800, 800)
        popup.wm_resizable(False, False)
        popup.wm_transient(self.master)
        popup.configure(fg_color="white")

        frameTextbox = customtkinter.CTkFrame(popup)
        frameTextbox.grid(row=6, column=0, sticky="nw", padx=10, pady=10)
        textbox = customtkinter.CTkTextbox(frameTextbox, width=400, corner_radius=0)
        textbox.grid(row=0, column=0, sticky="nsew")
        textbox.insert("0.0", "Some example text!\n")

        doneTextbox = customtkinter.CTkButton(frameTextbox, command=klaarKnopCommand).grid(row=1, column=0, sticky="nsew")

        frame_amount = customtkinter.CTkFrame(popup)
        frame_amount.grid(row=2, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_amount, text="Hoeveelheid robots:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_amount, values=[str(i) for i in range(1, 11)],
                                    command=change_val).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        frame_formation = customtkinter.CTkFrame(popup)
        frame_formation.grid(row=3, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_formation, text="Welke formatie:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_formation,
                                    values=["CROW-standaard", "Bocht", "Test"],
                                    command=changeFormation).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        frame_robot = customtkinter.CTkFrame(popup)
        frame_robot.grid(row=4, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_robot, text="Welke robot:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_robot,
                                    values=[str(i) for i in listOfRobotNames],
                                    command=changeStartRobot).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        customtkinter.CTkButton(popup, text="Configuratie klaar",
                                command=klaarKnopCommand,
                                border_color="black", border_width=2).grid(
            row=5, column=0, pady=10)
