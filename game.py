"""
Main game engine and TUI modules for the LKRhythm2 project.

This module handles the main game loop, frame rate capping, level selection,
and core application orchestration.
"""
import time
import textwrap
import typing
import threading
import os

import numpy as np
import pygame as pg

import display_grid as dg

import util
import menus
import settings
import player

ABOUT_TEXT = """ABOUT

LKRhythm II is a rhythm game.
I have been working on it for two years-it's really been a long
journey. This may well be the greatest thing I have ever built in
high school. I doubt I've ever spent this much time on anything else.
I hope you enjoy playing it as much as I enjoyed making it!

 - LemonKat

...this is it, the work is done, it is tangible, real. 

...it's quite an odd feeling, looking back.

...What does one do now, anyway? Should one be happy?


[press any button to close]"""

CREDITS_TEXT = """CREDITS
Software, Hardware, & Art/Design: LemonKat
Advisors: K.L., K.B.
Helpful internet people: std::kagami_ohayo, engine_machiner

Music Artists: niki, inabakumori, Anamanaguchi

This project would not have been possible without many others: 
The devlopers of every Python library, and every dependency;
those who built the tools to let us make music;
even the people at the cardboard factory.

And in general, every artist, every engineer, every maker who ever
was. All of your works have built up to this very moment and
countless others. May we ascend on these wings of silicon and steel,
wings we built by hand.

[press any button to close]"""

class FPSCap(dg.Module):
    """
    Module that caps the game's frame rate.
    
    Attributes:
        settings (settings.SettingsModule): Reference to game settings for 
            fetching the target FPS.
        clock (pg.time.Clock): The underlying Pygame clock used for timing.
    """
    def __init__(self, parent: dg.Module, settings: settings.SettingsModule) -> None:
        """
        Initializes the FPSCap module.
        
        Args:
            parent (dg.Module): The parent display_grid module.
            settings (settings.SettingsModule): The settings module to use 
                for frame rate capping.
        """
        super().__init__(parent)
        self.settings = settings
        self.clock = pg.time.Clock()

    def _tick(self) -> None:
        """Ticks the clock to maintain the set FPS according to settings."""
        self.clock.tick(self.settings.fps)

class LevelSelectModule(dg.Module):
    """
    The main level selection screen.
    
    Attributes:
        tracks (list[util.Track]): List of parsed tracks currently available.
        idx (int): The current selection index in the track list.
        panel_l (dg.SubGrid): The left panel showing the list of tracks.
        panel_r (dg.SubGrid): The right panel showing track details and waveform.
        settings (settings.SettingsModule): Reference to the game settings.
        player (player.PlayerModule): The module used for playing the selected track.
        fading (bool): Whether the preview audio is currently fading out.
        download_thread (typing.Optional[threading.Thread]): Async thread for 
            downloading missing assets.
        downloading_track_idx (int): Index of the track being downloaded.
        download_result (list[util.Track]): Shared list used to retrieve the 
            result of the asset download thread.
    """
    def __init__(self, parent: dg.Module, settings: settings.SettingsModule) -> None:
        """
        Initializes the LevelSelectModule.
        
        Args:
            parent (dg.Module): The parent display_grid module.
            settings (settings.SettingsModule): The shared settings module.
        """
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
        
        self.download_thread = None
        self.downloading_track_idx = -1
        self.download_result = []

    def start(self) -> None:
        """Reloads tracks and starts the level selection module."""
        self.tracks = util.reload_tracks()
        super().start()

    def preview(self) -> None:
        """
        Starts the audio preview for the selected track.
        Only runs if the audio is locally available and the player is paused.
        """
        if not self.tracks or self.idx >= len(self.tracks):
            return
            
        track = self.tracks[self.idx]
        if not self.player.paused or not os.path.exists(track.audio):
            return
        
        pg.mixer.music.set_volume(self.settings.vol / 100)
        pg.mixer.music.load(track.audio)
        pg.mixer.music.play(loops=0, start=track.preview[0], fade_ms=1000)

    def _tick(self) -> None:
        """
        Handles periodic logic for the level select screen.
        Checks for background download completion and handles preview loops.
        """
        if self.download_thread is not None and not self.download_thread.is_alive():
            if self.download_result:
                self.tracks[self.downloading_track_idx] = self.download_result[0]
            self.download_thread = None
            self.downloading_track_idx = -1
            self.download_result = []

        if not self.player.paused:
            return
        
        track = self.tracks[self.idx]
        if not os.path.exists(track.audio):
            return

        if not self.fading and pg.mixer.music.get_pos() / 1000 > track.preview[1] - track.preview[0] - 1:
            pg.mixer.music.fadeout(1000)
            self.fading = True

        elif pg.mixer.music.get_pos() / 1000 > track.preview[1] - track.preview[0]:
            pg.mixer.music.rewind()
            pg.mixer.music.play(loops=0, start=track.preview[0], fade_ms=1000)
            self.fading = False
    
    def _draw(self) -> None:
        """Draws the selection panel, track metadata, and waveforms to the grid."""
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
        
        desc = track.desc
        if self.downloading_track_idx == self.idx:
            desc = "DOWNLOADING ASSETS..."
        elif track.vis is None:
            desc = "PREVIEW NOT AVAILABLE\nSELECT TO DOWNLOAD"

        for i, line in enumerate(textwrap.wrap(desc, width=21)):
            self.panel_r.print(line, pos=(12 + i, 14))

        # waveform
        if track.vis is not None:
            t_play = pg.mixer.music.get_pos() / 1000 + track.preview[0]
            vis_frame = track.vis[int(t_play * 90)]
            for i, y in enumerate(vis_frame):
                self.panel_r.chars[i + 1, 2: int(12 * y ** 1.5) + 2] = ord("#")
        
    def _handle_event(self, event: dg.Event) -> bool:
        """
        Handles navigation and selection events for the track list.
        - 'a' / 'd': Navigate between tracks.
        - 'w' / ' ': Launch game or trigger asset download if missing.
        - 's': Exit back to main menu.
        
        Args:
            event (dg.Event): The event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
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
                if not os.path.exists(self.tracks[self.idx].audio):
                    if self.download_thread is None:
                        def _download(idx, track, out):
                            out.append(util.prepare_track_assets(track))
                        
                        self.downloading_track_idx = self.idx
                        self.download_thread = threading.Thread(
                            target=_download, 
                            args=(self.idx, self.tracks[self.idx], self.download_result)
                        )
                        self.download_thread.start()
                    return True

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
    """
    A module for displaying a static block of text within a border.
    
    Attributes:
        text (str): The body text to display.
    """
    def __init__(self, parent: dg.Module, text: str) -> None:
        """
        Initializes the TextboxModule.
        
        Args:
            parent (dg.Module): The parent display_grid module.
            text (str): The text content to display.
        """
        super().__init__(parent, box=[2, 4, 22, 76])
        self.text = text

    def _draw(self) -> None:
        """Draws the cleared grid with a border and the text content."""
        util.draw_border(self.grid)
        for i, line in enumerate(self.text.splitlines()):
            self.grid.print(line, pos=(i + 1, 2))

    def _handle_event(self, event: dg.Event) -> bool:
        """
        Closes the textbox on any 'awsd' or space key press.
        
        Args:
            event (dg.Event): The event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if isinstance(event, dg.KeyEvent) and event.key in "awsd ":
            self.stop()
            return True
        return False

class LKRhythmMain(dg.Module):
    """
    Main game entry point module.
    Orchestrates the Main Menu, Settings, About, and Level Selection.
    
    Attributes:
        settings (settings.SettingsModule): Shared game settings.
        level_select (LevelSelectModule): Track selection screen.
        about (TextboxModule): About text screen.
        credits (TextboxModule): Credits text screen.
        selector (menus.SelectorModule): Main menu selection module.
        fps_cap (FPSCap): Module for capping frame rate.
        running (bool): Main loop execution state.
    """
    def __init__(self, parent: dg.Module, box: typing.Optional[tuple[int, int, int, int]] = None) -> None:
        """
        Initializes the LKRhythmMain app orchestrator.
        
        Args:
            parent (dg.Module): The platform's MainModule.
            box (typing.Optional[tuple[int, int, int, int]]): Bounding box for the 
                entire game UI.
        """
        super().__init__(parent, box)

        self.settings = settings.SettingsModule(self)
        self.settings.stop()

        self.level_select = LevelSelectModule(self, self.settings)
        self.level_select.stop()

        self.about = TextboxModule(self, ABOUT_TEXT)
        self.about.stop()

        self.credits = TextboxModule(self, CREDITS_TEXT)
        self.credits.stop()

        self.selector = menus.SelectorModule(
            self,
            [12, 9, 17, 50],
            {
                "PLAY": menus.MenuOption(on_w=lambda: (self.level_select.start(), self.level_select.preview())),
                "SETTINGS": menus.MenuOption(on_w=lambda: (self.settings.start(), self.settings.selector.reset())),
                "ABOUT": menus.MenuOption(on_w=self.about.start),
                "CREDITS": menus.MenuOption(on_w=self.credits.start),
                "QUIT": menus.MenuOption(on_w=self.quit),
            }
        )

        self.fps_cap = FPSCap(self, self.settings)

        self.running = True

    def quit(self) -> None:
        """Exits the main game loop by setting running to False."""
        self.running = False

    def _draw(self) -> None:
        """Draws the main menu with logo, subtitle, and navigation tips."""
        util.draw_border(self.grid)
        self.grid.stamp("title", 4, 9)
        self.grid.print("A RHYTHM GAME BY LEMONKAT", pos=(10, 9))

        self.grid.print("←→ select", pos=(18, 9))
        self.grid.print("↑ enter", pos=(19, 9))

        self.grid.print("available at https://github.com/lemonkat/LKRhythm2", pos=(21, 9))

if __name__ == "__main__":
    dg.load_graphics("assets/")
    with dg.MainModule(os.get_terminal_size()[::-1], enforce_shape=False, mode="terminal") as main_module:
        i, j = (main_module.shape[0] - 24) // 2, (main_module.shape[1] - 80) // 2
        lkr_module = LKRhythmMain(main_module, [i, j, i + 24, j + 80])
        while lkr_module.running:
            main_module.tick()
            main_module.draw()
    print("Thanks for playing!")