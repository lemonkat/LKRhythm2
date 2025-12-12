import time
import textwrap

import numpy as np
import pygame as pg

import display_grid as dg

import util
import menus
import settings
import player

with open("about.txt") as f:
    about_text = f.read()

with open("credits.txt") as f:
    credits_text = f.read()

class FPSCap(dg.Module):
    def __init__(self, parent: dg.Module, settings: settings.SettingsModule) -> None:
        super().__init__(parent)
        self.settings = settings
        self.idx = 0
        self.data = np.zeros(10, dtype=np.float32)
        self.t_last = time.time()

    def _tick(self) -> None:
        self.data[self.idx] = time.time() - self.t_last
        time.sleep(max(0, 1 / self.settings.fps - np.mean(self.data)))
        self.idx = (self.idx + 1) % 10
        self.t_last = time.time()

class LevelSelectModule(dg.Module):
    def __init__(self, parent: dg.Module, settings: settings.SettingsModule) -> None:
        super().__init__(parent)
        self.tracks = util.reload_tracks()

        if not pg.get_init():
            pg.init()
        pg.mixer.music.unload()

        self.idx = 0
        self.panel_l = dg.SubGrid(self.grid, 2, 4, 22, 34)
        self.panel_r = dg.SubGrid(self.grid, 2, 33, 22, 76)

        self.settings = settings
        self.player = player.PlayerModule(self, settings)
        self.player.stop()

        self.fading = False

    def preview(self) -> None:
        self.tracks = util.reload_tracks()
        if not self.player.paused:
            return
        track = self.tracks[self.idx]
        
        pg.mixer.music.set_volume(self.settings.vol / 100)
        pg.mixer.music.load(track.audio)
        pg.mixer.music.play(loops=0, start=track.preview[0], fade_ms=1000)

    def _tick(self) -> None:
        if not self.player.paused:
            return
        
        track = self.tracks[self.idx]
        if not self.fading and pg.mixer.music.get_pos() / 1000 > track.preview[1] - track.preview[0] - 1:
            pg.mixer.music.fadeout(1000)
            self.fading = True

        elif pg.mixer.music.get_pos() / 1000 > track.preview[1] - track.preview[0]:
            pg.mixer.music.rewind()
            pg.mixer.music.play(loops=0, start=track.preview[0], fade_ms=1000)
            self.fading = False
    
    def _draw(self) -> None:
        if not self.player.paused:
            return
        util.draw_border(self.grid)
        util.draw_border(self.panel_l)
        util.draw_border(self.panel_r)

        self.panel_l.print("SELECT TRACK", pos=(1, 2))

        for i, track in enumerate(self.tracks):
            self.panel_l.print(track.title, pos=(3 + i, 4))
        
        self.panel_l.print(">", pos=(3 + self.idx, 2))

        self.panel_l.print("←→ select", pos=(16, 2))
        self.panel_l.print("↑ enter", pos=(17, 2))
        self.panel_l.print("↓ back", pos=(18, 2))

        track = self.tracks[self.idx]

        self.panel_r.stamp("record", 1, 5)

        self.panel_r.print(track.title, pos=(5, 14))
        self.panel_r.print(track.artist, pos=(6, 14))
        self.panel_r.print(("★" * track.difficulty).ljust(3), "|", dg.format_time(track.length), pos=(7, 14))
        for i, line in enumerate(textwrap.wrap(track.desc, width=21)):
            self.panel_r.print(line, pos=(12 + i, 14))

        # waveform
        t_play = pg.mixer.music.get_pos() / 1000 + track.preview[0]
        vis_frame = track.vis[int(t_play * 90)]
        for i, y in enumerate(vis_frame):
            self.panel_r.chars[i + 1, 2: int(12 * y ** 1.5) + 2] = ord("#")
        
    def _handle_event(self, event: dg.Event) -> None:
        if isinstance(event, dg.KeyEvent):
            if event.key == "a":
                self.idx = (self.idx - 1) % len(self.tracks)
                self.preview()
                return True
            elif event.key == "d":
                self.idx = (self.idx + 1) % len(self.tracks)
                self.preview()
                return True
            elif event.key in "w ":
                pg.mixer.music.stop()
                pg.mixer.music.unload()
                self.player.load_track(self.tracks[self.idx])
                self.player.start()
                return True
            elif event.key in "s":
                pg.mixer.music.stop()
                pg.mixer.music.unload()
                self.stop()
                return True
        return False

class TextboxModule(dg.Module):
    def __init__(self, parent: dg.Module, text: str) -> None:
        super().__init__(parent, box=[2, 4, 22, 76])
        self.text = text

    def _draw(self) -> None:
        util.draw_border(self.grid)
        for i, line in enumerate(self.text.splitlines()):
            self.grid.print(line, pos=(i + 1, 2))

    def _handle_event(self, event: dg.KeyEvent) -> bool:
        if isinstance(event, dg.KeyEvent) and event.key in "awsd ":
            self.stop()
            return True
        return False

class LKRhythmMain(dg.Module):
    def __init__(self, parent: dg.Module) -> None:
        super().__init__(parent)

        self.settings = settings.SettingsModule(self)
        self.settings.stop()

        self.level_select = LevelSelectModule(self, self.settings)
        self.level_select.stop()

        self.about = TextboxModule(self, about_text)
        self.about.stop()

        self.credits = TextboxModule(self, credits_text)
        self.credits.stop()

        self.selector = menus.SelectorModule(
            self,
            [12, 9, 17, 50],
            {
                "PLAY": lambda: (self.level_select.start(), self.level_select.preview()),
                "SETTINGS": lambda: (self.settings.start(), self.settings.selector.reset()),
                "ABOUT": self.about.start,
                "CREDITS": self.credits.start,
                "QUIT": self.quit,
            }
        )

        self.fps_cap = FPSCap(self, self.settings)

        self.running = True

    def quit(self) -> None:
        self.running = False

    def _draw(self) -> None:
        util.draw_border(self.grid)
        self.grid.stamp("title", 4, 9)
        self.grid.print("A RHYTHM GAME BY LEMONKAT", pos=(10, 9))

        self.grid.print("←→ select", pos=(18, 9))
        self.grid.print("↑ enter", pos=(19, 9))

        self.grid.print("available at https://github.com/lemonkat/LKRhythm2", pos=(21, 9))

if __name__ == "__main__":
    dg.load_graphics("assets/")
    with dg.MainModule((24, 80), enforce_shape=False, mode="terminal") as main_module:
        lkr_module = LKRhythmMain(main_module)
        while lkr_module.running:
            main_module.tick()
            main_module.draw()
    print("Thanks for playing!")