
import display_grid as dg

import util
import menus

class SettingsModule(dg.Module):
    def __init__(self, parent):
        super().__init__(parent, [4, 19, 18, 62])
        self.selector = menus.SelectorModule(
            self,
            [3, 3, 7, 20],
            {
                "Fall speed:": (self._spd_down, self._spd_up),
                "FPS:": (self._fps_down, self._fps_up),
                "Volume:": (self._vol_down, self._vol_up),
                "Back": self.stop,
            }
        )
        self.spd = 10
        self.fps = 60
        self.vol = 100

    def _draw(self) -> None:
        util.draw_border(self.grid)
        self.grid.print("SETTINGS", pos=(1, 3))

        self.grid.print(f"{self.spd}0%", pos=(3, 18))
        self.grid.print(self.fps, pos=(4, 11))
        self.grid.print(f"{self.vol}%", pos=(5, 14))

        self.grid.print("←→ select", pos=(8, 3))
        self.grid.print("↑↓ edit", pos=(9, 3))
    
    def _spd_down(self) -> None:
        self.spd = max(1, self.spd - 1)

    def _spd_up(self) -> None:
        self.spd = min(20, self.spd + 1)

    def _fps_down(self) -> None:
        self.fps = {30: 30, 60: 30, 120: 60}[self.fps]

    def _fps_up(self) -> None:
        self.fps = {30: 60, 60: 120, 120: 120}[self.fps]

    def _vol_down(self) -> None:
        self.vol = max(0, self.vol - 10)

    def _vol_up(self) -> None:
        self.vol = min(100, self.vol + 10)