"""
Settings management module for the LKRhythm2 project.
This module handles the game configuration such as note speed, FPS, and volume.
"""
import display_grid as dg

import util
import menus

class SettingsModule(dg.Module):
    """
    A TUI module for managing game settings like fall speed, FPS, and volume.
    
    Attributes:
        selector (menus.SelectorModule): The menu selector for settings options.
        spd (int): Note fall speed multiplier (1-20).
        fps (int): Target frame rate (30 or 60).
        vol (int): Master volume level (0-100).
    """
    def __init__(self, parent: dg.Module) -> None:
        """
        Initializes the SettingsModule.
        
        Args:
            parent (dg.Module): The parent display_grid module.
        """
        super().__init__(parent, [4, 19, 18, 62])
        self.selector = menus.SelectorModule(
            self,
            [3, 3, 7, 20],
            {
                "Fall speed:": menus.MenuOption(on_s=self._spd_down, on_w=self._spd_up),
                "FPS:": menus.MenuOption(on_s=self._fps_down, on_w=self._fps_up),
                "Volume:": menus.MenuOption(on_s=self._vol_down, on_w=self._vol_up),
                "Back": menus.MenuOption(on_w=self.stop),
            }
        )
        self.spd = 10
        self.fps = 60
        self.vol = 100

    def _draw(self) -> None:
        """Draws the settings menu UI, displaying current values and keyboard tips."""
        util.draw_border(self.grid)
        self.grid.print("SETTINGS", pos=(1, 3))

        self.grid.print(f"{self.spd}0%", pos=(3, 18))
        self.grid.print(self.fps, pos=(4, 11))
        self.grid.print(f"{self.vol}%", pos=(5, 14))

        self.grid.print("←→ select", pos=(8, 3))
        self.grid.print("↑↓ edit", pos=(9, 3))
    
    def _spd_down(self) -> None:
        """Decreases the note fall speed down to a minimum of 1."""
        self.spd = max(1, self.spd - 1)

    def _spd_up(self) -> None:
        """Increases the note fall speed up to a maximum of 20."""
        self.spd = min(20, self.spd + 1)

    def _fps_down(self) -> None:
        """Cycles the frame rate cap down (currently 60 -> 30)."""
        self.fps = {30: 30, 60: 30}[self.fps]

    def _fps_up(self) -> None:
        """Cycles the frame rate cap up (currently 30 -> 60)."""
        self.fps = {30: 60, 60: 60}[self.fps]

    def _vol_down(self) -> None:
        """Decreases the master volume by 10% increments."""
        self.vol = max(0, self.vol - 10)

    def _vol_up(self) -> None:
        """Increases the master volume by 10% increments."""
        self.vol = min(100, self.vol + 10)