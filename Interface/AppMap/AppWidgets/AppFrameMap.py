from encodings import mac_turkish
from tkinter import W
from tkinter.font import nametofont
import customtkinter
from tkintermapview import TkinterMapView
import math
from PIL import Image, ImageDraw, ImageTk

LINETAG = 0
ARROWLENGTH = 50


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master, sendCallback):
        super().__init__(master)

        self.sendMessageCallback = sendCallback
        # Make column grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Make row grids
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        # Map widget
        self.map_widget = TkinterMapView(self, corner_radius=5, database_path="map_tiles.db")
        self.map_widget.grid(row=1, column=0, columnspan=3, sticky="nswe", padx=(10, 10), pady=(0, 0))

        # Label
        self.label = customtkinter.CTkLabel(
            self,
            text="Map",
            fg_color='#01a6f8',
            width=100,
            height=20,
            font=('Bold', 28),
            corner_radius=5
        )
        self.label.grid(row=0, column=0, sticky="nw", padx=(8, 8), pady=(5, 5))

        # Mouse wheel binding
        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")

        # Control frame
        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        self.map_label = customtkinter.CTkLabel(self.control_frame, text="Tile Server:", anchor="w")
        self.map_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

        # Option menu
        self.map_option_menu = customtkinter.CTkOptionMenu(
            self.control_frame,
            values=["Maps normal", "Maps satellite"],
            command=self.change_map
        )
        self.map_option_menu.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nw")

        # Default map
        self.map_widget.set_tile_server(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            max_zoom=21
        )
        self.map_widget.set_position(52.0116, 4.3571)
        self.map_option_menu.set("Maps satellite")

        self.MAX_ZOOM = 21

        self.after(500, self._draw_scale)

        self.map_widget.add_right_click_menu_command(
            label="Add Marker",
            command=self.AddMarker,
            pass_coords=True
        )
        ### calculate positions button and testing switch button that goes to the correct function 
        self.controlFramePositionButtons = customtkinter.CTkFrame(self)
        self.controlFramePositionButtons.grid(row=2, column=1, sticky="nw", padx=10, pady=10)

        self.calculatePositionsButton = customtkinter.CTkButton(self.controlFramePositionButtons, text="Bereken overige posities", command=self.CalculatePositions,
                                                                border_color="black", border_width=2)
        self.calculatePositionsButton.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        self.testPositionModeVar = customtkinter.StringVar(value="on")
        self.testPositionsSwitch = customtkinter.CTkSwitch(self, text="Test mode",variable=self.testPositionModeVar, onvalue="True", offvalue=None,
                                                           border_color="black", border_width=2)
        self.testPositionsSwitch.grid(row=2,column=2, padx=10, pady=10, sticky="nw")

        self.calculatePositionsButton = customtkinter.CTkButton(self.controlFramePositionButtons, text="Verwijder berekende coördinaten", command=self.DeletePositions,
                                                                border_color="black", border_width=2, fg_color="red")
        self.calculatePositionsButton.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

        
        self.calculatePositionsButton = customtkinter.CTkButton(self.controlFramePositionButtons, text="Stuur posities naar robots", command=self.SendMessagesToRobots,
                                                                border_color="black", border_width=2, fg_color="green")
        self.calculatePositionsButton.grid(row=2, column=0, padx=10, pady=10, sticky="nw")

        self.markersDict = {}
        self.marker_lines = {}

        # Redraw lines on resize
        #self.map_widget.canvas.bind("<Configure>", self.DrawMarkerLines)
        self.addingMarker = False
        self.map_widget.canvas.bind("<ButtonRelease-1>", self._on_pan_end, add="+")

        self.map_widget.canvas.bind("<B1-Motion>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<Button-1>", self._on_pan_end, add="+")


    def change_map(self, new_map: str):
        if new_map == "Maps normal":
            self.MAX_ZOOM = 20
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                max_zoom=20
            )
        elif new_map == "Maps satellite":
            self.MAX_ZOOM = 21
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                max_zoom=21
            )

    def _on_scroll(self, event):
        self.after(50, self._enforce_zoom)
        #self.DrawMarkerLines()
        self.after(70, self.DrawMarkerLines)

    def _on_pan_end(self, event):
        self.after(70, self.DrawMarkerLines)

    def _enforce_zoom(self):
        if self.map_widget.zoom > self.MAX_ZOOM:
            self.map_widget.set_zoom(self.MAX_ZOOM)

    def _draw_scale(self):
        canvas = self.map_widget.canvas
        canvas.delete("scale")

        w = self.map_widget.winfo_width()
        h = self.map_widget.winfo_height()

        if w < 10 or h < 10:
            self.after(200, self._draw_scale)
            return

        x1, y1 = 20, h - 30
        x2, y2 = 120, h - 30

        meters = self._pixels_to_meters(100)

        canvas.create_line(x1, y1, x2, y2, fill="white", width=3, tags="scale")
        canvas.create_line(x1, y1 - 5, x1, y1 + 5, fill="white", width=3, tags="scale")
        canvas.create_line(x2, y2 - 5, x2, y2 + 5, fill="white", width=3, tags="scale")

        canvas.create_text(
            (x1 + x2) // 2,
            y1 - 10,
            text=f"{meters:.0f} m",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="scale"
        )

        self.after(500, self._draw_scale)

    def _pixels_to_meters(self, pixels):
        zoom = self.map_widget.zoom
        lat = self.map_widget.get_position()[0]
        meters_per_pixel = (156543.03 * math.cos(math.radians(lat))) / (2 ** zoom)
        return pixels * meters_per_pixel

    def DrawMarkerLines(self, event=None):
        if self.addingMarker:
            return
        """Redraw all marker lines after zoom/pan"""
        for marker, data in list(self.marker_lines.items()):
            line_tag, direction = data

            if not marker.deleted:
                canvas_x, canvas_y = marker.get_canvas_pos(marker.position)

                self.map_widget.canvas.delete(line_tag)
                angle_rad = math.radians(direction)
                endx = canvas_x + ARROWLENGTH * math.cos(angle_rad)
                endy = canvas_y + ARROWLENGTH * math.sin(angle_rad)

                self.map_widget.canvas.create_line(
                    canvas_x, canvas_y,
                    endx, endy,
                    fill="green",
                    width=5,
                    tags=line_tag,
                    arrow = customtkinter.LAST
                )

        #self.after(10, self.DrawMarkerLines)

    def AddMarker(self, coords, direction=None, markerText="new mark"):
        self.addingMarker = True

        print("adding new marker:", coords)
        self.DeletePositions(markerText)

        newMarker = self.map_widget.set_marker(coords[0], coords[1], text=markerText)
        self.markersDict[newMarker] = markerText

        self.map_widget.update_idletasks()

        line_tag = markerText
        self.marker_lines[newMarker] = [line_tag, direction]

        self.addingMarker = False
        self.DrawMarkerLines()

    def CalculatePositions(self):
        ##check of er wel robots op de map zijn
        print("calculateButtonPressed")
        if not self.markersDict:
            return
        first_marker = list(self.markersDict.keys())[0]
        lat, lon = first_marker.position

        # pak richting (bearing) uit jouw dict
        direction = self.marker_lines[first_marker][1]

        if direction is None:
            print("Geen richting ingesteld")
            return

        distance = 5  # meters (bijv. 100m vooruit)
        normalizedDirection = self.NormalisePositionDegreeValues(direction, 1)

        new_lat, new_lon = self.calculate_destination(lat, lon, normalizedDirection, distance)

        # nieuwe marker toevoegen
        self.AddMarker((new_lat, new_lon), direction, markerText="calculated")

    def calculate_destination(self, lat, lon, bearing, distance):
        R = 6371000  # straal van de aarde in meters

        # omzetten naar radialen
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        theta = math.radians(bearing)
        delta = distance / R

        # formule toepassen
        lat2 = math.asin(
            math.sin(lat1) * math.cos(delta) +
            math.cos(lat1) * math.sin(delta) * math.cos(theta)
        )

        lon2 = lon1 + math.atan2(
            math.sin(theta) * math.sin(delta) * math.cos(lat1),
            math.cos(delta) - math.sin(lat1) * math.sin(lat2)
        )

        # terug naar graden
        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)

        return lat2, lon2

    def NormalisePositionDegreeValues(self, degrees, situation):
        ##situation 1 is north is pointing 0 degrees, from 270 degrees
        if situation == 1 and degrees is not None:
            degrees += 90
            return degrees
    
    def DeletePositions(self, nameToDelete="calculated"):
        markersToDelete = [key for key, val in self.markersDict.items() if nameToDelete in val]
        markerLinesToDelete = [key for key, val in self.marker_lines.items() if nameToDelete in val]

        for key in markersToDelete:
            del self.markersDict[key]
            key.delete()
        for key in markerLinesToDelete:
            del self.marker_lines[key]


    def SendMessagesToRobots(self, robotName=None, msgField=None, msg=None):
        coordsDict = {}
        for marker, name in self.markersDict.items():
            if "calc" in name:
                coords = marker.position
                print("print coords dit zijn: ", coords)
                coordsDict[name]= coords

        print("coordsdict = ", coordsDict)
        self.sendMessageCallback(coordsDict)


