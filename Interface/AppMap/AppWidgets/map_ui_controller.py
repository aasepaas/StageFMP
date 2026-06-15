"""
MapUIController - Manages UI components and layout.

Responsibility: Creating and managing all UI components (buttons, frames, menus).
"""

import customtkinter
from typing import Callable, Optional, Tuple


class MapUIController:
    """Controls UI components and their layout.
    
    Handles:
    - Creating UI components (buttons, labels, frames)
    - Managing UI state (test mode toggle)
    - Layout of all UI elements
    - Callback management
    """
    
    def __init__(self, parent_frame, on_change_map: Callable,
                 on_calculate: Callable, on_delete: Callable,
                 on_send: Callable, on_test_toggle: Callable):
        """Initialize UI controller.
        
        Args:
            parent_frame: Parent CTkFrame for UI components
            on_change_map: Callback when map tile type changes
            on_calculate: Callback when calculate button pressed
            on_delete: Callback when delete button pressed
            on_send: Callback when send button pressed
            on_test_toggle: Callback when test mode toggled
        """
        self.parent_frame = parent_frame
        self.on_change_map = on_change_map
        self.on_calculate = on_calculate
        self.on_delete = on_delete
        self.on_send = on_send
        self.on_test_toggle = on_test_toggle
        
        # UI components
        self.title_label: Optional[customtkinter.CTkLabel] = None
        self.control_frame: Optional[customtkinter.CTkFrame] = None
        self.map_option_menu: Optional[customtkinter.CTkOptionMenu] = None
        self.reset_button: Optional[customtkinter.CTkButton] = None
        self.position_buttons_frame: Optional[customtkinter.CTkFrame] = None
        self.test_mode_var: Optional[customtkinter.StringVar] = None
        
        # Create components
        self._create_components()
    
    # ────────────────────────────────────────────────────────────────
    # Component creation
    # ────────────────────────────────────────────────────────────────
    
    def _create_components(self) -> None:
        """Create all UI components."""
        self._create_title_label()
        self._create_control_frame()
        self._create_reset_button()
        self._create_position_buttons_frame()
    
    def _create_title_label(self) -> None:
        """Create title label."""
        self.title_label = customtkinter.CTkLabel(
            self.parent_frame,
            text="Map:",
            fg_color='#01a6f8',
            width=100,
            height=20,
            font=('Bold', 28),
            corner_radius=5
        )
    
    def _create_control_frame(self) -> None:
        """Create control frame with map selection."""
        from AppMap.AppWidgets.UIBuilder import UIBuilder
        
        self.control_frame, self.map_option_menu = UIBuilder.create_control_frame(
            self.parent_frame,
            self.on_change_map
        )
    
    def _create_reset_button(self) -> None:
        """Create reset button."""
        self.reset_button = customtkinter.CTkButton(
            self.control_frame,
            text="Reset",
            border_color="black",
            border_width=2,
            fg_color="red"
            # Command will be set by orchestrator
        )
        self.reset_button.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="nw")
    
    def _create_position_buttons_frame(self) -> None:
        """Create position calculation and control buttons frame."""
        from AppMap.AppWidgets.UIBuilder import UIBuilder
        
        self.position_buttons_frame, self.test_mode_var = \
            UIBuilder.create_position_buttons_frame(
                self.parent_frame,
                calculate_callback=self.on_calculate,
                delete_callback=self.on_delete,
                send_callback=self.on_send,
                switch_test_callback=self.on_test_toggle
            )
    
    # ────────────────────────────────────────────────────────────────
    # Layout management
    # ────────────────────────────────────────────────────────────────
    
    def layout_ui(self, map_widget) -> None:
        """Layout all UI components on the parent frame.
        
        Organizes the spatial arrangement of:
        - Title label (row 0)
        - Map widget (row 1, spans columns)
        - Control frames (row 2)
        
        Args:
            map_widget: The map widget to layout
        """
        # Title label
        if self.title_label:
            self.title_label.grid(
                row=0, column=0, sticky="nw",
                padx=(8, 8), pady=(5, 5)
            )
        
        # Map widget
        map_widget.grid(
            row=1, column=0, columnspan=3, sticky="nswe",
            padx=(10, 10), pady=(0, 0)
        )
        
        # Control frame (left)
        if self.control_frame:
            self.control_frame.grid(
                row=2, column=0, sticky="nw",
                padx=10, pady=10
            )
        
        # Position buttons frame (right)
        if self.position_buttons_frame:
            self.position_buttons_frame.grid(
                row=2, column=1, columnspan=2, sticky="nwse",
                padx=10, pady=10
            )
    
    # ────────────────────────────────────────────────────────────────
    # Component accessors
    # ────────────────────────────────────────────────────────────────
    
    def set_reset_button_command(self, command: Callable) -> None:
        """Set the reset button command.
        
        Args:
            command: Callable to execute on button press
        """
        if self.reset_button:
            self.reset_button.configure(command=command)
    
    def set_map_option_selection(self, option: str) -> None:
        """Set the current map option selection.
        
        Args:
            option: Map option name to select
        """
        if self.map_option_menu:
            self.map_option_menu.set(option)
    
    def get_map_option_selection(self) -> Optional[str]:
        """Get the current map option selection.
        
        Returns:
            Current map option or None
        """
        if self.map_option_menu:
            return self.map_option_menu.get()
        return None
    
    def get_test_mode(self) -> str:
        """Get the current test mode value.
        
        Returns:
            Test mode string value ("0" or "1")
        """
        if self.test_mode_var:
            return self.test_mode_var.get()
        return "0"
    
    def is_test_mode_enabled(self) -> bool:
        """Check if test mode is enabled.
        
        Returns:
            True if test mode is on, False otherwise
        """
        return self.get_test_mode() == "1"
    
    # ────────────────────────────────────────────────────────────────
    # State management
    # ────────────────────────────────────────────────────────────────
    
    def enable_controls(self) -> None:
        """Enable all UI controls."""
        self._set_controls_state(state="normal")
    
    def disable_controls(self) -> None:
        """Disable all UI controls (e.g., during processing)."""
        self._set_controls_state(state="disabled")
    
    def _set_controls_state(self, state: str) -> None:
        """Set state of all interactive controls.
        
        Args:
            state: Widget state ("normal" or "disabled")
        """
        if self.map_option_menu:
            self.map_option_menu.configure(state=state)
        
        if self.reset_button:
            self.reset_button.configure(state=state)
        
        # Disable buttons in position frame
        if self.position_buttons_frame:
            for child in self.position_buttons_frame.winfo_children():
                if isinstance(child, customtkinter.CTkButton):
                    child.configure(state=state)
    
    # ────────────────────────────────────────────────────────────────
    # Utility methods
    # ────────────────────────────────────────────────────────────────
    
    def get_ui_config(self) -> dict:
        """Get current UI configuration.
        
        Returns:
            Dictionary with current UI state
        """
        return {
            "map_selection": self.get_map_option_selection(),
            "test_mode": self.is_test_mode_enabled(),
            "controls_enabled": True  # Could track actual state
        }
    
    def show_message(self, message: str, title: str = "Info") -> None:
        """Show an info message to the user.
        
        Args:
            message: Message text
            title: Window title (not used in current implementation)
        """
        print(f"{title}: {message}")
        # Could be extended to show actual message boxes