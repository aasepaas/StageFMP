from tkinter import W
import customtkinter
from tkintermapview import TkinterMapView
import math


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ###make the column grids for which the widgets will sit in
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ###make the column rows for which the widgets will sit in
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        ###make the map widget and give it a local db file for quicker loading times
        self.map_widget = TkinterMapView(self, corner_radius=5,database_path="map_tiles.db")
        ###place the map in the middle row and for both columns
        self.map_widget.grid(row=1, column=0,columnspan=2, sticky="nswe", padx=(10, 10), pady=(0, 0))

        ###map text above the map widget
        self.label = customtkinter.CTkLabel(self, text="Map",
                                            fg_color='#01a6f8', 
                                            width=100,
                                            height=20,
                                            font=('Bold', 28),
                                            corner_radius=5)
        self.label.grid(row=0, column=0, sticky="nw", padx=(8,8), pady=(5,5))

        ###mouse wheel binding for zooming in and out of the map widget 
        ###send it to the onscroll function for an extra check
        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")

        ###make the map selector placeholder
        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)
        self.map_label = customtkinter.CTkLabel(self.control_frame, text="Tile Server:", anchor="w")
        self.map_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="nw")
        ###make the map selector option menu
        self.map_option_menu = customtkinter.CTkOptionMenu(self.control_frame, values=["Maps normal", "Maps satellite"],
                                                           command=self.change_map)
        self.map_option_menu.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nw")


        #self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.set_tile_server("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", max_zoom=21)
        self.map_widget.set_position(52.0116, 4.3571)
        self.map_option_menu.set("Maps satellite")
        self.MAX_ZOOM = 21
        self.after(500, self._draw_scale)
        self.map_widget.add_right_click_menu_command(label="Add Marker",
                                        command=self.AddMarker,
                                        pass_coords=True)
        self.markersDict = {}

        


    def change_map(self, new_map: str):
        if new_map == "Maps normal":
            self.MAX_ZOOM = 20
            self.map_widget.set_tile_server("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", max_zoom=20)
        elif new_map == "Maps satellite":
            self.MAX_ZOOM=21
            self.map_widget.set_tile_server("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", max_zoom=21)


    def _on_scroll(self, event):
        self.after(50, self._enforce_zoom)
        #self.after(51, self._draw_scale)

    def _enforce_zoom(self):
        if self.map_widget.zoom > self.MAX_ZOOM:
            self.map_widget.set_zoom(self.MAX_ZOOM)

    def _draw_scale(self):
        canvas = self.map_widget.canvas
        canvas.delete("scale")

        w = self.map_widget.winfo_width()
        h = self.map_widget.winfo_height()
    
        # Check of widget al geladen is
        if w < 10 or h < 10:
            self.after(200, self._draw_scale)
            return

        x1, y1 = 20, h - 30
        x2, y2 = 120, h - 30

        meters = self._pixels_to_meters(100)

        canvas.create_line(x1, y1, x2, y2, fill="white", width=3, tags="scale")
        canvas.create_line(x1, y1-5, x1, y1+5, fill="white", width=3, tags="scale")
        canvas.create_line(x2, y2-5, x2, y2+5, fill="white", width=3, tags="scale")
        canvas.create_text((x1+x2)//2, y1-10, 
                           text=f"{meters:.0f} m", 
                           fill="white", font=("Arial", 10, "bold"), tags="scale")
    
        # Herteken elke 500ms zodat het niet verdwijnt na map refresh
        #self.after(500, self._draw_scale)

    def _pixels_to_meters(self, pixels):
        zoom = self.map_widget.zoom
        lat = self.map_widget.get_position()[0]
        # Formule: meters per pixel op bepaalde zoom en breedtegraad
        meters_per_pixel = (156543.03 * math.cos(math.radians(lat))) / (2 ** zoom)
        return pixels * meters_per_pixel

    def AddMarker(self, coords, direction, markerText="new mark"):
        print("adding new marker: ", coords)
        newMarker = self.map_widget.set_marker(coords[0], coords[1], text=markerText)

        self.markersDict[newMarker] = markerText
        print(self.markersDict)