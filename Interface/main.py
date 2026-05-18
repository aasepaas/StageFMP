#from mainInterface import App
from calendar import setfirstweekday
from sqlite3 import SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE
from token import COMMA
from AppMap import app
from time import sleep
import customtkinter as ctk

from MQTTClient import MQTTClient  
from customLogger import customLogger
import math



ca_certs=r"C:\stage_HBO3_FMN\certificaten\ca_root.pem"
certfile=r"C:\stage_HBO3_FMN\certificaten\GUI-cert.pem"
keyfile=r"C:\stage_HBO3_FMN\certificaten\GUI-key.pem"

# # import tkinter as tk


# def closest_point_on_segment(px, py, x1, y1, x2, y2):
#     # vector AB
#     dxAB = x2 - x1
#     dyAB = y2 - y1

#     # vector AP
#     dxAP = px - x1
#     dyAP = py - y1

#     # lengte kwadraat van AB
#     length_sqAP = dxAB*dxAP + dyAB*dyAP
    
#     length_sqAB = (x2-x1)**2 + (y2-y1)**2

#     # projectie factor
#     t = length_sqAP/  length_sqAB

#     # clamp tussen 0 en 1 (belangrijk!)
#     #t = max(0, min(1, t))


#     # bereken punt
#     closest_x = x1 + t * dxAB
#     closest_y = y1 + t * dyAB

#     return (closest_x, closest_y)

# def draw_infinite_line(canvas, x1, y1, x2, y2, **kwargs):
#     # Large number to ensure the line goes off-screen
#     length = 10000 
    
#     # Calculate the vector between the two points
#     dx = x2 - x1
#     dy = y2 - y1
    
#     # Calculate extended endpoints in both directions
#     # Start point = p1 - (vector * length)
#     # End point = p1 + (vector * length)
#     ex1 = x1 - dx * length
#     ey1 = y1 - dy * length
#     ex2 = x1 + dx * length
#     ey2 = y1 + dy * length
    
#     return canvas.create_line(ex1, ey1, ex2, ey2, **kwargs)

# root = tk.Tk()
# canvas = tk.Canvas(root, width=400, height=400, bg='white')
# canvas.pack()

# # Draw infinite line through (100, 100) and (150, 120)
# #draw_infinite_line(canvas, 100, 100, 150, 120, fill='blue', width=2)

# oval = canvas.create_oval(50,50, 50, 50, fill="red")

# pts = [100,100,150,120]  # lijn
# px, py = 50, 50         # punt

# cx, cy = closest_point_on_segment(px, py, *pts)

# print("closest point:", cx, cy)

# canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="blue")
# canvas.create_line(px, py, cx, cy, fill="red", dash=(2,2))

# root.mainloop()


# class App(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.grid_rowconfigure(0, weight=1)  # configure grid system
#         self.grid_columnconfigure(0, weight=1)

#         self.textbox = ctk.CTkTextbox(master=self, width=400, corner_radius=0)
#         self.textbox.grid(row=0, column=0, sticky="nsew")
#         self.textbox.insert("0.0", "Some example text!\n")
#         self.doneTextbox = ctk.CTkButton(self, command=self.buttonPressed).grid(row=1, column=1, sticky="nsew")

#     def buttonPressed(self):
#         print(self.textbox.get("0.0", "end"))


# app = App()
# app.mainloop()

if __name__ == "__main__":

    def on_message(client, userdata, msg):
       bericht = msg.payload.decode()
       topic = msg.topic
       print(f"Bericht ontvangen op '{topic}': {bericht}")




    MQTTClient1 = MQTTClient("localhost", 8883, "GUI", ca_certs, certfile, keyfile)
    app = app(MQTTClient1)

    MQTTClient1.SetMessageHandler(app.MessageHandler)
    MQTTClient1.connectToBroker()
    MQTTClient1.listen_for_messages()
    sleep(0.1)
    MQTTClient1.subscribe_to_topic("Robots/#", qos=1)



    app.startGUI()