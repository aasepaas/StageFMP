"""
PositionCalculatorManager - Manages robot position calculations.

Responsibility: Calculate robot positions based on formation type and place them on map.
"""

from typing import Dict, List, Optional, Tuple


class PositionCalculatorManager:
    """Manages robot position calculations and placement.
    
    Handles:
    - Position calculations for different formations
    - Building offset polylines
    - Placing calculated positions on map
    - Formation strategy dispatch
    """
    
    def __init__(self, marker_manager, road_data_manager,
                 offset_polyline_manager, overlay_renderer):
        """Initialize position calculator manager.
        
        Args:
            marker_manager: MarkerManager for marker operations
            road_data_manager: RoadDataManager for road data
            offset_polyline_manager: OffsetPolylineManager for offset polylines
            overlay_renderer: MapOverlayRenderer for placing markers
        """
        self.marker_manager = marker_manager
        self.road_data_manager = road_data_manager
        self.offset_polyline_manager = offset_polyline_manager
        self.overlay_renderer = overlay_renderer
    
    def calculate_and_place_positions(
        self,
        distance: int = 10,
        amount: int = 1,
        mother_bot_pos: int = 1,
        formation: str = "Standaard 10m afstand"
    ) -> bool:
        """Calculate robot positions and place them on map.
        
        Process:
        1. Get first marker position (start point)
        2. Build offset polyline from that point
        3. Calculate positions based on formation type
        4. Place calculated markers on map
        5. Draw offset roads
        
        Args:
            distance: Distance between robots in meters (default: 10)
            amount: Number of robots to calculate (default: 1)
            mother_bot_pos: Position of mother robot (default: 1)
            formation: Formation type (default: "Standaard 10m afstand")
        
        Returns:
            True if calculation successful, False otherwise
        """
        # Get first marker position
        first_marker = self.marker_manager.get_first_marker()
        if first_marker is None:
            print("No first marker found for position calculation")
            return False
        
        lat, lon = first_marker.position
        direction = self.marker_manager.marker_lines[first_marker][1]
        
        # Build offset polyline (the line used for calculations)
        self.offset_polyline_manager.build_offset_polylines(
            lat, lon, self.road_data_manager.road_polylines
        )
        
        offset_polyline = self.offset_polyline_manager.get_offset_polyline()
        if offset_polyline is None:
            print("Could not build offset polyline for position calculation")
            return False
        
        # Calculate positions based on formation type
        positions = self._calculate_by_formation(
            lat, lon, direction, offset_polyline,
            distance, amount, formation
        )
        
        if not positions:
            print("Position calculation returned no positions")
            return False
        
        # Place calculated positions on map
        for i, (pos_lat, pos_lon, pos_direction) in enumerate(positions, 1):
            self.overlay_renderer.add_marker_with_styling(
                (pos_lat, pos_lon),
                pos_direction,
                f"calculated{i}"
            )
        
        # Draw the offset polyline
        zoom_level = int(self.overlay_renderer.map_widget.zoom)
        self.overlay_renderer.draw_offset_roads(zoom_level)
        
        print(f"Successfully calculated and placed {len(positions)} positions")
        return True
    
    def _calculate_by_formation(
        self,
        lat: float,
        lon: float,
        direction: float,
        offset_polyline: List,
        distance: int,
        amount: int,
        formation: str
    ) -> List[Tuple[float, float, float]]:
        """Calculate positions based on formation type.
        
        Different formations use different calculation strategies:
        - CROW formation: Tight formation, specific geometry
        - Standard formation: Linear spacing along polyline
        
        Args:
            lat: Starting latitude
            lon: Starting longitude
            direction: Starting direction in degrees
            offset_polyline: Polyline to calculate along
            distance: Distance between robots
            amount: Number of robots
            formation: Formation type name
        
        Returns:
            List of (lat, lon, direction) tuples
        """
        from AppMap.AppWidgets.PositionCalculator import PositionCalculator
        
        print(f"Calculating positions for formation: {formation}")
        
        if "CROW" in formation:
            # CROW formation - special geometry
            positions = PositionCalculator.calculate_crow_positions(
                lat, lon, direction, offset_polyline, amount
            )
        else:
            # Standard formation - linear spacing
            positions = PositionCalculator.calculate_positions(
                lat, lon, direction, offset_polyline, distance, amount
            )
        
        return positions
    
    def get_calculated_positions(self) -> Dict:
        """Get all calculated positions currently on map.
        
        Returns:
            Dictionary of calculated positions indexed by marker
        """
        return self.marker_manager.get_calculated_positions()
    
    def clear_calculated_positions(self) -> None:
        """Clear all calculated position markers from map."""
        self.overlay_renderer._delete_position("calculated")
    
    def validate_calculation_parameters(
        self,
        distance: int,
        amount: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate calculation parameters.
        
        Args:
            distance: Distance between robots
            amount: Number of robots
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if amount <= 0:
            return False, "Amount must be greater than 0"
        
        if amount > 100:
            return False, "Amount must be less than 100"
        
        if distance < 0:
            return False, "Distance cannot be negative"
        
        if distance > 1000:
            return False, "Distance must be less than 1000 meters"
        
        return True, None
    
    def get_supported_formations(self) -> List[str]:
        """Get list of supported formation types.
        
        Returns:
            List of formation name strings
        """
        return [
            "Standaard 10m afstand",
            "Standaard 20m afstand",
            "Standaard 5m afstand",
            "CROW formatie",
            "Lijn formatie"
        ]