from geopy.geocoders import Nominatim
from AppMap.AppWidgets.UIBuilder import UIBuilder


class LocationManager:
    """Manages lat,lon to address and displays incident location."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="my_app")
        self.incident_frame = None
    
    def reverse_geocode(self, lat, lon):
        """Reverse geocode coordinates to address."""
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}")
            return location.raw.get("address", {})
        except Exception as e:
            print(f"Geocoding error: {e}")
            return {}
    
    def create_incident_frame(self, master, location_dict, go_to_callback):
        """Create and display incident location frame."""
        if self.incident_frame is not None:
            return self.incident_frame
        
        road = location_dict.get("road", "Unknown")
        city = location_dict.get("city", "Unknown")
        state = location_dict.get("state", "Unknown")
        location_text = f"{road}, {city}, {state}"
        
        self.incident_frame = UIBuilder.create_incident_location_frame(
            master, location_text, go_to_callback
        )
        return self.incident_frame
    
    def destroy_incident_frame(self):
        """Destroy incident location frame."""
        if self.incident_frame is not None:
            self.incident_frame.grid_forget()
            self.incident_frame.destroy()
            self.incident_frame = None
