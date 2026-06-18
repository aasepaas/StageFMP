from abc import ABC, abstractmethod
from typing import Callable, Optional, Tuple


class MapEventCallbacks(ABC):
    """Interface for map event callbacks."""
    
    @abstractmethod
    def on_add_marker(self, coords: Tuple[float, float]):
        """Called when user adds marker.

        """
        pass
    
    @abstractmethod
    def on_scroll(self, event=None):
        """Called when user scrolls (zooms).
        

        """
        pass
    
    @abstractmethod
    def on_pan_end(self, event=None):
        """Called when pan ends.
        

        """
        pass


class MapEventHandler:
    """Binds and delegates map interaction events.
    
    """
    
    def __init__(self, map_widget, callbacks: MapEventCallbacks):
        """Initialize event handler.

        """
        self.map_widget = map_widget
        self.callbacks = callbacks
    
    def bind_events(self) -> None:
        """Bind all map event handlers.
        

        """
        # Right-click menu
        self.map_widget.add_right_click_menu_command(
            label="Add Marker",
            command=self.callbacks.on_add_marker,
            pass_coords=True
        )
        
        # Scroll/zoom events
        self.map_widget.bind("<MouseWheel>", self._on_scroll_wrapper)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll_wrapper, add="+")
        
        # Pan events
        self.map_widget.canvas.bind(
            "<ButtonRelease-1>", self._on_pan_wrapper, add="+"
        )
        self.map_widget.canvas.bind(
            "<B1-Motion>", self._on_pan_wrapper, add="+"
        )
        self.map_widget.canvas.bind(
            "<Button-1>", self._on_pan_wrapper, add="+"
        )
    
    def _on_scroll_wrapper(self, event=None) -> None:
        """Wrapper for scroll event."""
        self.callbacks.on_scroll(event)
    
    def _on_pan_wrapper(self, event=None) -> None:
        """Wrapper for pan event."""
        self.callbacks.on_pan_end(event)
