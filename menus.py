"""
TUI menu selection modules for the LKRhythm2 project.
This module provides a flexible selection system used in the main menu, 
settings menu, and pause screen.
"""
import typing
    
import display_grid as dg

class MenuOption(typing.NamedTuple):
    """
    Represents an entry in a SelectorModule menu.
    
    Attributes:
        on_w (typing.Callable[[], None]): Callback triggered when the 'w' or 
            space key is pressed (primary action).
        on_s (typing.Optional[typing.Callable[[], None]]): Optional callback 
            triggered when the 's' key is pressed (secondary action).
            If None, 's' presses are propagated to the parent module.
    """
    on_w: typing.Callable[[], None]
    on_s: typing.Optional[typing.Callable[[], None]] = None

class SelectorModule(dg.Module):
    """
    A TUI module for selecting from a list of options using 'a'/'d' keys (left/right).
    
    Attributes:
        options (list[tuple[str, MenuOption]]): A list of menu labels and their 
            corresponding actions.
        idx (int): The current selection index.
        ptr (str): The selection cursor string.
    """
    def __init__(
        self, 
        parent: dg.Module,
        box: tuple[int, int, int, int],
        options: dict[str, typing.Union[typing.Callable[[], None], tuple[typing.Callable[[], None], typing.Callable[[], None]], MenuOption]],
        ptr: str = " > ",
    ) -> None:
        """
        Initializes the SelectorModule.
        
        Args:
            parent (dg.Module): The parent display_grid module.
            box (tuple[int, int, int, int]): The (y0, x0, y1, x1) bounding box.
            options (dict[str, typing.Union[typing.Callable[[], None], tuple[typing.Callable[[], None], typing.Callable[[], None]], MenuOption]]): 
                A dictionary mapping labels to actions.
            ptr (str): The selection cursor string.
        """
        super().__init__(parent, box)
        self.options: list[tuple[str, MenuOption]] = []
        # Convert mixed input types into a uniform list of (label, MenuOption)
        for name, opt in options.items():
            if isinstance(opt, MenuOption):
                self.options.append((name, opt))
            elif isinstance(opt, tuple):
                # Backwards compatibility: (secondary_action, primary_action)
                self.options.append((name, MenuOption(on_s=opt[0], on_w=opt[1])))
            else:
                self.options.append((name, MenuOption(on_w=opt)))
        
        self.idx = 0
        self.ptr = ptr

    def reset(self) -> None:
        """Resets the selection index to the first option."""
        self.idx = 0
    
    def _draw(self) -> None:
        """Draws the selection cursor and labels on the grid."""
        i = 0
        for idx, option in enumerate(self.options):
            if idx == self.idx:
                self.grid.print(self.ptr, pos=(i, 0))
            for line in option[0].splitlines():
                self.grid.print(line, pos=(i, len(self.ptr)))
                i += 1

    def _handle_event(self, event: dg.Event) -> bool:
        """
        Handles menu navigation and selection.
        - 'a' / 'd': Previous/Next option.
        - 'w' / ' ': Trigger primary action.
        - 's': Trigger secondary action if defined, else propagate to parent.
        
        Args:
            event (dg.Event): The event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if not isinstance(event, dg.KeyEvent) or not self.options:
            return False

        opt = self.options[self.idx][1]

        if event.key == "a":
            self.idx = (self.idx - 1) % len(self.options)
            return True
        elif event.key == "d":
            self.idx = (self.idx + 1) % len(self.options)
            return True
        elif event.key in "w ":
            opt.on_w()
            return True
        elif event.key == "s" and opt.on_s is not None:
            opt.on_s()
            return True
        
        return False
