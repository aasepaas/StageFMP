import threading
from typing import Optional, Tuple


class MapRoadManager:
    """Manages road data fetching and refresh scheduling.
    """
    
    def __init__(self, map_widget, map_view_controller, road_data_manager, reset_callback):
        """Initialize road manager.
       
        """
        self.map_widget = map_widget
        self.map_view_controller = map_view_controller
        self.road_data_manager = road_data_manager
        self.reset_callback = reset_callback
        
        # Scheduling
        self.road_refresh_job: Optional[int] = None
        
        # Constants
        self.ROAD_DRAW_ZOOM = 17  # Only fetch when zoomed in
    
    def schedule_refresh(self, delay_ms: int = 400) -> None:
        """Schedule road data refresh.
        
        """
        result = None
        if self.road_refresh_job is not None:
            self.map_widget.after_cancel(self.road_refresh_job)
        
        self.road_refresh_job = self.map_widget.after(
            delay_ms, self.refresh_roads
        )
        #print("RESULTTTTTTTTTTT", result)
        #return result
    
    def refresh_roads(self):
        """Refresh road data based on current viewport.
        
        Process:
        1. Get current zoom level
        2. Check if zoomed in enough to draw roads
        3. Get current viewport bbox
        4. Check if cached roads are sufficient
        5. If not, fetch new roads asynchronously
        """
        self.road_refresh_job = None
        
        # Normalize zoom level
        zoom = self.map_widget.zoom
        zoom_int = int(zoom)
        self.map_widget.set_zoom(zoom_int)
        
        # Don't fetch roads if zoomed out too far
        if zoom_int < self.ROAD_DRAW_ZOOM:
            self.reset_callback()
            return False
        
        # Get current viewport bounding box
        bbox = self.map_view_controller.get_viewport_bbox()
        if bbox is None:
            return
        
        # Check if cached roads are sufficient
        if self._cached_roads_valid(bbox):
            return
        
        # Fetch new roads if not already fetching
        if not self.road_data_manager.road_fetch_running:
            self._fetch_roads_async(bbox)
    
    def _cached_roads_valid(self, current_bbox: Tuple) -> bool:
        """Check if cached roads are valid for current viewport.
        
        """
        # Check if we have cached roads
        if (self.road_data_manager.road_fetch_bbox is None or
            not self.road_data_manager.has_data()):
            return False
        
        # Check if cached bbox contains current bbox
        return self.map_view_controller.bbox_contains(
            self.road_data_manager.road_fetch_bbox, current_bbox
        )
    
    def _fetch_roads_async(self, bbox: Tuple) -> None:
        """Fetch roads asynchronously using threading.
        
        """
        self.road_data_manager.road_fetch_running = True
        
        lat_min, lon_min, lat_max, lon_max = bbox
        
        # Expand bbox by 30% to prefetch for panning
        dlat = (lat_max - lat_min) * 0.30
        dlon = (lon_max - lon_min) * 0.30
        
        fetch_bbox = (
            lat_min - dlat,
            lon_min - dlon,
            lat_max + dlat,
            lon_max + dlon
        )
        
        # Start background fetch thread
        thread = threading.Thread(
            target=self.road_data_manager.fetch_roads_thread,
            args=(fetch_bbox,),
            daemon=True,
            name="RoadFetchThread"
        )
        thread.start()
    
    def cancel_refresh(self) -> None:
        """Cancel any pending refresh.

        """
        if self.road_refresh_job is not None:
            self.map_widget.after_cancel(self.road_refresh_job)
            self.road_refresh_job = None
    
    def wait_for_fetch_completion(self, timeout_ms: int = 5000) -> bool:
        """Wait for any ongoing road fetch to complete.
        """
        import time
        
        start_time = time.time()
        timeout_s = timeout_ms / 1000.0
        
        while self.road_data_manager.road_fetch_running:
            if time.time() - start_time > timeout_s:
                return False
            time.sleep(0.1)
        
        return True
    
    def get_road_stats(self) -> dict:
        """Get current road data statistics.
        """
        return {
            "has_data": self.road_data_manager.has_data(),
            "is_fetching": self.road_data_manager.road_fetch_running,
            "fetch_bbox": self.road_data_manager.road_fetch_bbox,
            "polyline_count": len(self.road_data_manager.road_polylines)
                if self.road_data_manager.road_polylines else 0,
            "refresh_scheduled": self.road_refresh_job is not None
        }