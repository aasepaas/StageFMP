import customtkinter
from tkintermapview import TkinterMapView


class UIBuilder:
    """Builds and manages UI components."""
    
    @staticmethod
    def create_map_widget(master):
        """Create and configure map widget."""
        map_widget = TkinterMapView(master, corner_radius=5, database_path="map_tiles.db")
        map_widget.bind("<MouseWheel>", lambda e: None)
        map_widget.canvas.bind("<MouseWheel>", lambda e: None, add="+")
        return map_widget
    
    @staticmethod
    def create_control_frame(master, change_map_callback):
        """Create map type control frame."""
        control_frame = customtkinter.CTkFrame(master)
        
        customtkinter.CTkLabel(control_frame, text="Soort map:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        
        map_option_menu = customtkinter.CTkOptionMenu(
            control_frame,
            values=["Map normaal", "Map satelliet"],
            command=change_map_callback
        )
        map_option_menu.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="nw")
        
        customtkinter.CTkLabel(control_frame, text="Reset scherm:", anchor="w").grid(
            row=4, column=0, padx=10, pady=(5, 0), sticky="nw")
        
        return control_frame, map_option_menu
    
    @staticmethod
    def create_position_buttons_frame(master, calculate_callback, delete_callback, 
                                     send_callback, switch_test_callback, on_home_robots_callback):
        """Create position calculation buttons frame."""
        frame = customtkinter.CTkFrame(master)
        
        customtkinter.CTkButton(
            frame, text="Stuur robots terug naar weginspecteur",
            command=on_home_robots_callback, border_color="black", border_width=2, fg_color="blue"
        ).grid(row=1, column=2, padx=10, pady=10, sticky="nw")

        customtkinter.CTkButton(
            frame, text="Bereken overige posities",
            command=calculate_callback, border_color="black", border_width=2
        ).grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        
        test_mode_var = customtkinter.StringVar(value=False)
        customtkinter.CTkSwitch(
            frame, text="Test mode", variable=test_mode_var,
            onvalue=True, offvalue=False,
            border_color="black", border_width=2, command=switch_test_callback
        ).grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        
        customtkinter.CTkButton(
            frame, text="Verwijder berekende coordinaten",
            command=delete_callback, border_color="black", border_width=2, fg_color="red"
        ).grid(row=0, column=1, padx=10, pady=10, sticky="nw")
        
        customtkinter.CTkButton(
            frame, text="Stuur posities naar robots",
            command=send_callback, border_color="black", border_width=2, fg_color="green"
        ).grid(row=0, column=2, padx=10, pady=10, sticky="nw")
        
        return frame, test_mode_var
    
    @staticmethod
    def create_incident_location_frame(master, location_text, go_to_callback):
        """Create incident location display frame."""
        frame = customtkinter.CTkFrame(master)
        
        customtkinter.CTkLabel(
            frame, text="Incidentlocatie:",
            font=("Arial", 14, "bold"),
            fg_color='#01a6f8',
            corner_radius=5,
            text_color="black"
        ).grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        
        customtkinter.CTkLabel(
            frame, text=location_text,
            fg_color='#01a6f8',
            corner_radius=5,
            text_color="black"
        ).grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")
        
        customtkinter.CTkButton(
            frame, text="Ga naar positie",
            command=go_to_callback, border_color="black", border_width=2, fg_color="green"
        ).grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        
        return frame
