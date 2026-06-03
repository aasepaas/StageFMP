from tkinter import Canvas
from turtle import update
import customtkinter
from PIL import Image, ImageDraw
import os

class AppScrolFrameRobots(customtkinter.CTkScrollableFrame):
    """Frame that contains the list of robots self that is shown on the UI."""
    def __init__(self, master):
        super().__init__(master)
        self.currentRow = 0
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.IMAGE_PATH = os.path.join(BASE_DIR, 'robotScreenshot.png')
        self.base_image = Image.open(self.IMAGE_PATH)  # Bewaar originele image
        self.robotFrames = {}  # Dictionary om frames en labels bij te houden per robot
    
    def AddNewRobotToFrame(self, robotName):
        control_frame = customtkinter.CTkFrame(self)
        
        # Maak image met status indicator
        img_with_status = self._create_image_with_status(self.base_image, None)
        ctk_image = customtkinter.CTkImage(
            light_image=img_with_status,
            dark_image=img_with_status,
            size=(75, 75)
        )
        
        img_label = customtkinter.CTkLabel(control_frame, text="", image=ctk_image)
        img_label.image = ctk_image  # Referentie behouden
        
        control_frame.grid(row=self.currentRow, column=0, padx=(10, 10), pady=(10, 10))
        img_label.grid(row=0, column=0, rowspan=2, padx=(10, 10), pady=(10, 10))
        
        text_label = customtkinter.CTkLabel(control_frame, text=robotName, font=("Arial", 18, "bold"))
        text_label.grid(row=0, column=1, padx=(10, 10), pady=(10, 10), sticky="n")
        status = "online"
        statusText = customtkinter.CTkLabel(control_frame, text=f"status: {status}", font=("Arial", 14), fg_color="green")
        statusText.grid(row=1, column=1, padx=(10, 10), pady=(10, 10), sticky="n")
        # Bewaar referenties
        self.robotFrames[robotName] = {
            'frame': control_frame,
            'img_label': img_label,
            'text_label': text_label,
            'status': None,
            'status_label': statusText
        }
        
        self.currentRow += 1
    
    def _create_image_with_status(self, base_img, status):
        """Maak een kopie van de image met status indicator cirkel"""
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
    
        # Bepaal kleur op basis van status
        if status in ["done", "online"]:
            color = "green"
            show_cross = False
        elif status == "error":
            color = "red"
            show_cross = True
        else:
            # Geen status indicator
            return img
    
        # Teken cirkel rechtsboven (pas positie aan naar wens)
        img_width, img_height = img.size
        circle_radius = int(img_width * 0.15)  # 15% van breedte
    
        # Positie rechtsboven met wat marge
        x = img_width - circle_radius - 5
        y = 5
    
        # Teken cirkel met witte rand
        draw.ellipse(
            [x - circle_radius, y, x + circle_radius, y + circle_radius * 2],
            fill=color,
            outline="black",
            width=7
        )
    
        # Teken wit kruis voor error status
        if show_cross:
            # Center van de cirkel
            center_x = x
            center_y = y + circle_radius
        
            # Kruis grootte (iets kleiner dan de cirkel)
            cross_size = int(circle_radius * 0.7)
        
            # Teken X (twee diagonale lijnen)
            # Lijn van linksboven naar rechtsonder
            draw.line(
                [center_x - cross_size, center_y - cross_size,
                 center_x + cross_size, center_y + cross_size],
                fill="white",
                width=6
            )
        
            # Lijn van rechtsboven naar linksonder
            draw.line(
                [center_x + cross_size, center_y - cross_size,
                 center_x - cross_size, center_y + cross_size],
                fill="white",
                width=6
            )
    
        return img

    def UpdateRobotFrame(self, robotName, updateValueField, updateValue):
        """Update de robot frame met nieuwe status"""
        if robotName not in self.robotFrames:
            print(f"Robot {robotName} not found in frames")
            return
        
        robot_data = self.robotFrames[robotName]
        
        # Als het een status update is
        if updateValueField.lower() == "status":
            robot_data['status'] = updateValue
            robot_data['status_label'].configure(text=f"Status is: {updateValue} ", fg_color="red") if updateValue == "error" else robot_data['status_label'].configure(text=f"Status is: {updateValue} ", fg_color="green")
            
            # Maak nieuwe image met status indicator
            img_with_status = self._create_image_with_status(self.base_image, updateValue)
            
            # Update de CTkImage
            new_ctk_image = customtkinter.CTkImage(
                light_image=img_with_status,
                dark_image=img_with_status,
                size=(75, 75)
            )
            
            # Update label
            robot_data['img_label'].configure(image=new_ctk_image)
            robot_data['img_label'].image = new_ctk_image  # Referentie behouden
            
            print(f"Updated {robotName} status to {updateValue}")

    def ResetList(self):
        robotList = [k for k,v in self.robotFrames.items()]
        for k in robotList:
            robot_data = self.robotFrames[k]
            robot_data['frame'].destroy()
            del self.robotFrames[k]