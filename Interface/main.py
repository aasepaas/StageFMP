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





if __name__ == "__main__":
    
    # def menu_callback(choice):
    #     print(f"Gekozen optie: {choice}")

    # def LinePlotter(start_point, angle_deg, length):
    #     x, y = start_point
    #     angle_rad = math.radians(angle_deg)
    #     endx = x + length * math.cos(angle_rad)
    #     endy = y + length * math.sin(angle_rad)

    #     canvas.create_line(x, y, endx, endy, arrow=ctk.LAST)

    # app = ctk.CTk()
    # app.geometry("900x1620")


    # canvas = ctk.CTkCanvas(app, width = 1620, height=900)
    # #canvas.create_line(1420, 850, 1420, 800, fill="green", 
    #  #       width=5)
    # LinePlotter((1420, 850), 450, 50)
    # canvas.pack()


    # app.mainloop()


    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")


    app = app()

    MQTTClient1 = MQTTClient("MQTTserver", 8883, "GUI", ca_certs, certfile, keyfile, on_message_handler=app.MessageHandler)
    MQTTClient1.connectToBroker()


    MQTTClient1.listen_for_messages()
    sleep(0.1)
    MQTTClient1.subscribe_to_topic("Robots/#")


    app.startGUI()