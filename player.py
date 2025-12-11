import time
import textwrap
import typing
    
import pygame as pg

import display_grid as dg

import util
import menus
import settings

PERFECT_RANGE = -0.1, 0.1
GOOD_RANGE = -0.25, 0.25
FAILED_RANGE = -0.4, float("inf")

class Player:
    def __init__(self, track: util.Track) -> None:
        self.track = track

        self.channels = {key: [t for t, k in track.notes if k == key] for key in util.KEYS}
        self.states = {note: util.NoteState.OPEN for note in track.notes}
        self.state_counts = {
            util.NoteState.PERFECT: 0, 
            util.NoteState.GOOD: 0, 
            util.NoteState.FAILED: 0, 
            util.NoteState.MISSED: 0,
        }
        self.indices = {key: 0 for key in util.KEYS}

        self.combo = self.best_combo = 0
        self.score = 0

        if not pg.get_init():
            pg.init()

        pg.mixer.music.unload()
        pg.mixer.music.load(track.audio)
        pg.mixer.music.play()
        pg.mixer.music.pause()

    def time(self) -> float:
        return pg.mixer.music.get_pos() / 1000
    
    def play(self) -> None:
        pg.mixer.music.unpause()
    
    def pause(self) -> None:
        pg.mixer.music.pause()

    def hit(self, key: str) -> util.NoteState:
        t_hit = self.time()
        note = self.next(key)
        if note is None:
            return util.NoteState.OPEN
        
        t_note, _ = note
        
        if t_note + PERFECT_RANGE[0] < t_hit < t_note + PERFECT_RANGE[1]:
            self.hit_note(note, util.NoteState.PERFECT)
            self.score += 20
            return util.NoteState.PERFECT
        elif t_note + GOOD_RANGE[0] < t_hit < t_note + GOOD_RANGE[1]:
            self.hit_note(note, util.NoteState.GOOD)
            self.score += 15
            return util.NoteState.GOOD
        elif t_note + FAILED_RANGE[0] < t_hit:
            self.hit_note(note, util.NoteState.FAILED)
            return util.NoteState.FAILED
        
        return util.NoteState.OPEN

    def hit_note(self, note: util.Note, state: util.NoteState) -> None:
        self.states[note] = state
        self.state_counts[state] += 1
        self.indices[note.key] += 1
        if state in [util.NoteState.FAILED, util.NoteState.MISSED]:
            self.combo = 0
        else:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)

    def next(self, key: str) -> typing.Optional[util.Note]:
        if self.indices[key] >= len(self.channels[key]):
            return None
        return util.Note(self.channels[key][self.indices[key]], key)

    def update(self) -> util.NoteState:
        t_play = self.time()
        missed = False
        for key in util.KEYS:
            while True:
                note = self.next(key)
                if note is None or note.time > t_play + GOOD_RANGE[0]:
                    break
                self.hit_note(note, util.NoteState.MISSED)
                missed = True
        return util.NoteState.MISSED if missed else util.NoteState.OPEN
    
    @property
    def acc(self) -> float:
        n_played = sum(self.state_counts.values())
        if not n_played:
            return 1.0
        return (self.state_counts[util.NoteState.PERFECT] + 0.5 * self.state_counts[util.NoteState.GOOD]) / n_played

class PauseModule(dg.Module):
    def __init__(
        self,
        parent: "PlayerModule", 
    ) -> None:
        super().__init__(parent, box=[4, 19, 18, 62])
        self.parent = parent
        self.selector_a = menus.SelectorModule(
            self,
            [3, 2, 7, 14],
            {
                "Resume": parent.start_play,
                "Restart": parent.restart_play,
                "Settings": parent.settings.start,
                "Quit": parent.close,
            }
        )
        self.selector_b = menus.SelectorModule(
            self,
            [3, 2, 6, 14],
            {
                "Restart": parent.restart_play,
                "Settings": parent.settings.start,
                "Quit": parent.close,
            }
        )

        self.is_open = True
    
    def open(self) -> None:
        self.is_open = True
        self.start()

    def close(self) -> None:
        self.is_open = False
    
    def _tick(self) -> None:
        if self.parent.done:
            self.selector_a.stop()
            self.selector_b.start()
            
        else:
            self.selector_a.start()
            self.selector_b.stop()
    
    def _draw(self) -> None:
        util.draw_border(self.grid)
        track_player = self.parent.track_player
        track = track_player.track

        if self.parent.done:
            if track_player.acc == 1.0:
                self.grid.print("PERFECT", pos=(1, 3))
            elif track_player.combo == len(track.notes):
                self.grid.print("FULL COMBO", pos=(1, 3))
            elif track_player.acc >= 0.95:
                self.grid.print("GREAT", pos=(1, 3))
            elif track_player.acc >= 0.6:
                self.grid.print("GOOD", pos=(1, 3))
            else:
                self.grid.print("COMPLETE", pos=(1, 3))

        else:
            self.grid.print("PAUSED", pos=(1, 3))

        self.grid.print("←→ select", pos=(8, 3))
        self.grid.print("↑ enter", pos=(9, 3))
        self.grid.print("↓ back", pos=(10, 3))
        
        stats_grid = dg.SubGrid(self.grid, 0, 15, 14, 44)
        util.draw_border(stats_grid)
       
        stats_grid.print(track.title, "|", track.artist, pos=(1, 3))
        lines = textwrap.wrap(track.desc, 23)
        for i, line in enumerate(lines):
            stats_grid.print(line, pos=(i + 2, 3))
        stats_grid.print("SCORE:", track_player.score, pos=(5, 3))
        stats_grid.print("COMBO:", track_player.combo, pos=(6, 3))
        stats_grid.print("BEST COMBO:", track_player.best_combo, pos=(7, 3))
        stats_grid.print(f"ACCURACY: {track_player.acc * 100:>6.2f}%", pos=(8, 3))

        stats_grid.print("PERFECT:", track_player.state_counts[util.NoteState.PERFECT], pos=(10, 3))
        stats_grid.print("GOOD:", track_player.state_counts[util.NoteState.GOOD], pos=(11, 3))
        stats_grid.print("FAILED:", track_player.state_counts[util.NoteState.FAILED] + track_player.state_counts[util.NoteState.MISSED], pos=(12, 3))

    def _handle_event(self, event: dg.Event) -> bool:
        if isinstance(event, dg.KeyEvent):
            if event.key in [" ", "s"]:
                self.parent.start_play()
                return True
        return False
    
class PlayerModule(dg.Module):
    def __init__(
        self,
        parent: dg.Module, 
        settings: settings.SettingsModule,
        track: typing.Optional[util.Track] = None,
    ) -> None:
        super().__init__(parent)
        self.track_player = None if track is None else Player(track)
        self.settings = settings
        
        self.pause_menu = PauseModule(self)
        self.pause_menu.stop()

        self.t_start = float("inf")

        self.cur_msg = None
        self.t_msgclear = -1
        self.t_hitclear = {key: float("-inf") for key in util.KEYS}


    @property
    def done(self) -> bool:
        return self.track_player.time() >= self.track_player.track.length
    
    def load_track(self, track: util.Track) -> None:
        self.track_player = Player(track)
        self.track_player.pause()
        self.start_play()

    def start_play(self) -> None:
        self.pause_menu.stop()
        self.t_start = time.time() + 1.5

        self.cur_msg = None
        self.t_msgclear = -1
        self.t_hitclear = {key: float("-inf") for key in util.KEYS}
    
    def stop_play(self) -> None:
        self.pause_menu.start()
        self.track_player.pause()
        self.t_start = float("inf")

        self.cur_msg = None
        self.t_msgclear = -1

    def restart_play(self) -> None:
        self.track_player.pause()
        self.load_track(self.track_player.track)
        self.start_play()

    def close(self) -> None:
        self.track_player.pause()
        self.stop()
        self.parent.preview()

    def _set_msg(
        self, 
        msg: str, 
        dur: float,
        fg: typing.Optional[tuple[int, int, int]] = None,
        bg: typing.Optional[tuple[int, int, int]] = None,
        attrs: typing.Optional[int] = None,
    ) -> None:
        self.cur_msg = msg, fg, bg, attrs
        self.t_msgclear = self.track_player.time() + dur

    def _tick(self) -> None:
        t_real = time.time()
        t_play = self.track_player.time()

        pg.mixer.music.set_volume(self.settings.vol / 100)

        if t_real >= self.t_start:
            self.track_player.play()
        
        if self.t_msgclear < t_play:
            self.cur_msg = None
        
        if self.track_player.update() == util.NoteState.MISSED:
            self._set_msg(" FAILED", 0.8, fg=(200, 0, 0))
        
        if self.done:
            self.stop_play()

        
    def _handle_event(self, event: dg.Event) -> bool:
        t_play = self.track_player.time()
        if isinstance(event, dg.KeyEvent):
            if event.key == " ":
                self.stop_play()
                return True
            elif event.key in util.KEYS:
                self.t_hitclear[event.key] = t_play + 0.3
                state = self.track_player.hit(event.key)
                if state == util.NoteState.PERFECT:
                    self._set_msg("PERFECT", 0.6, fg=(255, 255, 0))
                if state == util.NoteState.GOOD:
                    self._set_msg("   GOOD", 0.6, fg=(0, 180, 255))
                if state == util.NoteState.FAILED:
                    self._set_msg(" FAILED", 0.6, fg=(230, 0, 0))
                return True
        return False
    
    def _draw_channel(self, key: str, t_play: float) -> None:
        col = 16 + 16 * util.KEYS.index(key)
        self.grid.chars[3:-5, col] = ord("|")
        self.grid.chars[-5, col] = ord("*")

        if key == util.KEYS[0]:
            self.grid.stamp("arrow_left", 20, col - 2)
        elif key == util.KEYS[1]:
            self.grid.stamp("arrow_down", 20, col - 2)
        elif key == util.KEYS[2]:
            self.grid.stamp("arrow_up", 20, col - 2)
        elif key == util.KEYS[3]:
            self.grid.stamp("arrow_right", 20, col - 2)

        self.grid.fg[20: 23, col - 2: col + 2] = 255 if self.t_hitclear[key] > t_play else 230

        for t_note in self.track_player.channels[key]:
            note = util.Note(t_note, key)
            state = self.track_player.states[note]
            if state in [util.NoteState.OPEN, util.NoteState.MISSED]:
                loc = 19 + self.settings.spd * (t_play - t_note)
                if loc >= 23 or loc <= 4:
                    continue
            
            else:
                loc = 19
                if t_play - t_note > 0.3:
                    continue
            
            color = {
                util.NoteState.OPEN: [255, 255, 0],
                util.NoteState.PERFECT: [255, 255, 0],
                util.NoteState.GOOD: [0, 180, 255],
                util.NoteState.FAILED: [230, 0, 0],
                util.NoteState.MISSED: [230, 0, 0],
            }[state]

            loc_int = int(loc)
            loc_frac = int(8 * (loc - loc_int))
            char = ord(dg.BLOCKS[8 - loc_frac])

            if 3 <= loc_int < 23:
                self.grid.fg[loc_int, col] = color
                self.grid.chars[loc_int, col] = char

            if loc_frac > 0 and 2 <= loc_int < 22:
                self.grid.fg[loc_int + 1, col] = self.grid.bg[loc_int + 1, col]
                self.grid.bg[loc_int + 1, col] = color
                self.grid.chars[loc_int + 1, col] = char
    
    def _draw(self) -> None:
        t_real = time.time()
        t_play = self.track_player.time()

        util.draw_border(self.grid)

        # stats bar
        util.draw_border(dg.SubGrid(self.grid, 0, 0, 3, 80))
        self.grid.print(self.track_player.track.title, "|", self.track_player.track.artist, pos=(1, 2))
        self.grid.print("SCORE:", self.track_player.score, pos=(1, 30))
        self.grid.print("COMBO:", self.track_player.combo, pos=(1, 44))
        self.grid.print(f"ACC: {self.track_player.acc * 100:>6.2f}%", pos=(1, 58))

        if self.cur_msg is not None:
            self.grid.print(
                self.cur_msg[0], 
                pos=(1, 71), 
                fg=self.cur_msg[1], 
                bg=self.cur_msg[2], 
                attrs=self.cur_msg[3],
            )

        # main graphics
        self.grid.chars[19, 1:-1] = ord("-")
        for key in util.KEYS:
            self._draw_channel(key, t_play)

        # countdown
        if self.t_start - 0.5 < t_real < self.t_start:
            self.grid.stamp("num_1", 4, 38)
        elif self.t_start - 1 < t_real < self.t_start - 0.5:
            self.grid.stamp("num_2", 4, 38)
        elif t_real < self.t_start - 1:
            self.grid.stamp("num_3", 4, 38)

        # waveform
        vis_frame = self.track_player.track.vis[int(t_play * 90)]
        for i, y in enumerate(vis_frame[:15]):
            y = int(12 * y ** 1.5)
            self.grid.chars[i + 4, 2: y + 2] = ord("#")
            self.grid.chars[i + 4, 77 - y: 77] = ord("#")

        for i, y in enumerate(vis_frame[15:]):
            y = int(12 * y ** 1.5)
            self.grid.chars[i + 20, 2: y + 2] = ord("#")
            self.grid.chars[i + 20, 77 - y: 77] = ord("#")

        # playback
        time_str = "{} / {}".format(
            dg.format_time(t_play).rjust(5),
            dg.format_time(self.track_player.track.length).rjust(5)
        )
        self.grid.print(time_str, pos=(3, 2))