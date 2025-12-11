import typing
    
import display_grid as dg

class SelectorModule(dg.Module):
    def __init__(
        self, 
        parent: dg.Module,
        box: tuple[int, int, int, int],
        options: dict[str, typing.Callable[[], None] | tuple[typing.Callable[[], None], typing.Callable[[], None]]],
        ptr: str = " > ",
    ) -> None:
        super().__init__(parent, box)
        self.options = list(options.items())
        self.idx = 0
        self.ptr = ptr
    
    def _draw(self):
        i = 0
        for idx, option in enumerate(self.options):
            if idx == self.idx:
                self.grid.print(self.ptr, pos=(i, 0))
            for line in option[0].splitlines():
                self.grid.print(line, pos=(i, len(self.ptr)))
                i += 1

    def _handle_event(self, event: dg.Event) -> None:
        if isinstance(self.options[self.idx][1], tuple):
            opt_s, opt_w = self.options[self.idx][1]
        else:
            opt_s, opt_w = None, self.options[self.idx][1]

        if isinstance(event, dg.KeyEvent):
            if event.key == "a":
                self.idx = (self.idx - 1) % len(self.options)
                return True
            elif event.key == "d":
                self.idx = (self.idx + 1) % len(self.options)
                return True
            elif event.key in "w ":
                opt_w()
                return True
            elif event.key in "s" and opt_s is not None:
                opt_s()
                return True
        return False
