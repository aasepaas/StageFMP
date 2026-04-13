from encodings import mac_turkish
from tkinter import W
import customtkinter
from tkintermapview import TkinterMapView
import math
from PIL import Image, ImageDraw, ImageTk

LINETAG = 0
ARROWLENGTH = 50


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Make column grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Make row grids
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        # Map widget
        self.map_widget = TkinterMapView(self, corner_radius=5, database_path="map_tiles.db")
        self.map_widget.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=(10, 10), pady=(0, 0))

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

        self.markersDict = {}
        self.marker_lines = {}

        # Redraw lines on resize
        #self.map_widget.canvas.bind("<Configure>", self.DrawMarkerLines)
        self.addingMarker = False

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
        self.DrawMarkerLines()
        #self.after(50, self.DrawMarkerLines)

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
        for marker, data in self.marker_lines.items():
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

        self.after(10, self.DrawMarkerLines)

    def AddMarker(self, coords, direction=None, markerText="new mark"):
        self.addingMarker = True
        print("adding new marker:", coords)
        possibleKeyMarker = [key for key, val in self.markersDict.items() if val == markerText]
        possibleKeyLineMarker = [key for key, val in self.marker_lines.items() if val[0] == markerText]
        #print("possiblelinemarker: ", possibleKeyLineMarker)
        if possibleKeyMarker and possibleKeyLineMarker:
            print("possible key verwijdering")
            del self.markersDict[possibleKeyMarker[0]]
            del self.marker_lines[possibleKeyLineMarker[0]]
            possibleKeyMarker[0].delete()



        newMarker = self.map_widget.set_marker(coords[0], coords[1], text=markerText)
        self.markersDict[newMarker] = markerText
        

        self.map_widget.update_idletasks()

        line_tag = markerText
        self.marker_lines[newMarker] = [line_tag, direction]

        print(self.markersDict)
        print(self.marker_lines)

        #self.after(100, self.DrawMarkerLines)
        self.addingMarker = False
        self.DrawMarkerLines()
 

