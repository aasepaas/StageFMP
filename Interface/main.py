#from mainInterface import App
from AppMap import app
from time import sleep
import customtkinter as ctk

from MQTTClient import MQTTClient  
from customLogger import customLogger
import math


ca_certs=r"C:\stage_HBO3_FMN\MQTT-container\emqx_setup\certs\ca_chain.pem"
certfile=r"C:\stage_HBO3_FMN\certificaten\GUI-cert.pem"
keyfile=r"C:\stage_HBO3_FMN\certificaten\GUI-key.pem"


# from tkinter import *



# def pop_up(listOfRobotNames, popupDataSubmit, root):
#     print(listOfRobotNames)
#     aantalRobots = 0

#     chosenSettings = {
#         "Aantal": None,
#         "Formatie":None,
#         "RobotStart": None}

#     def klaarKnopCommand():
#         if any(val == None for key, val in chosenSettings.items()):
#                print("selecteer alle waardes voor returneren")
#                return
#         popupDataSubmit(chosenSettings)
#         popup.destroy()


#     def change_val(value):
#         try:
#             int(value)
#             print("chosen amount= ", value)
#             chosenSettings["Aantal"] = value
#         except:
#             pass
#     def changeFormation(formation):
#         chosenSettings["Formatie"] = formation

#     def changeStartRobot(robotName):
#         chosenSettings["RobotStart"] = robotName

#     popup = ctk.CTkToplevel(root)
#     popup.title("Instellingen voor berekeningen")
#     popup.wm_maxsize(300, 400)
#     popup.wm_resizable(False, False)


#     #####frame voor kiezen hoeveelheid robots
#     control_frameOptionMenuChoise = ctk.CTkFrame(popup)
#     control_frameOptionMenuChoise.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

#     HvlheidRobotsLabel=ctk.CTkLabel(control_frameOptionMenuChoise, text="Hoeveelheid robots:", anchor="w").grid(
#             row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
#     map_option_menu = ctk.CTkOptionMenu(
#             control_frameOptionMenuChoise,
#             values=[str(i) for i in range(1,11)],
#             command=change_val
#         )
#     map_option_menu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

#     #####frame voor kiezen formatie
#     control_frameFormationChoise = ctk.CTkFrame(popup)
#     control_frameFormationChoise.grid(row=3, column=0, sticky="nw", padx=10, pady=10)

#     HvlheidRobotsLabel=ctk.CTkLabel(control_frameFormationChoise, text="Welke formatie:", anchor="w").grid(
#             row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
#     formationOptionMenu = ctk.CTkOptionMenu(
#             control_frameFormationChoise,
#             values=["CROW-standaard", "Bocht", "Test"],
#             command=changeFormation
#         )
#     formationOptionMenu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

#     #####frame voor kiezen welke robot zijn pos heeft gestuurd
#     control_frameCurrentRobotChoise = ctk.CTkFrame(popup)
#     control_frameCurrentRobotChoise.grid(row=4, column=0, sticky="nw", padx=10, pady=10)

#     welkeRobotsVal=ctk.CTkLabel(control_frameCurrentRobotChoise, text="Welke robot:", anchor="w").grid(
#             row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
#     huidigeRobotOptionMenu = ctk.CTkOptionMenu(
#             control_frameCurrentRobotChoise,
#             values=[str(i) for i in listOfRobotNames],
#             command=changeStartRobot
#         )
#     huidigeRobotOptionMenu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

#     klaarKnop = ctk.CTkButton(popup, text="Configuratie klaar",command=klaarKnopCommand)
#     klaarKnop.grid(row=5, column=0, pady=10)

# robotNames =[]

# app = Tk()

# def receiveValueFromPopup(data):
#     print(data)
    

# def goToPopup():
#     pop_up(robotNames, receiveValueFromPopup, app)


    


# app.title("Main Frame")
# label = Label(app, text = "This is the main frame")
# label.grid()
# btn = Button(app, text= "Open the popup window", command = goToPopup)
# btn.grid(row=1)
# robotNames = ["robot1", "robot5", "motherbot"]

# app.mainloop()




if __name__ == "__main__":

    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")




    MQTTClient1 = MQTTClient("MQTTserver", 8883, "GUI", ca_certs, certfile, keyfile)
    app = app(MQTTClient1)

    MQTTClient1.SetMessageHandler(app.MessageHandler)
    MQTTClient1.connectToBroker()
    MQTTClient1.listen_for_messages()
    sleep(0.1)
    MQTTClient1.subscribe_to_topic("Robots/#", qos=1)



    app.startGUI()