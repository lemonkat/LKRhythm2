import requests
import typing
import enum
import os

import numpy as np

import display_grid as dg

import wave_vis

KEYS = "aswd"

class Note(typing.NamedTuple):
    time: float
    key: str

class Track(typing.NamedTuple):
    title: str
    artist: str
    difficulty: int
    desc: str
    audio: str
    notes: list[Note]
    length: float
    preview: tuple[float, float]
    vis: np.ndarray[np.float32]

def parse_track(data: typing.Iterable[str]) -> Track:
    title = "N/A"
    artist = "N/A"
    desc = "N/A"
    audio = "N/A"
    difficulty = 2
    preview_start = 0
    preview_stop = float("inf")
    notes = []
    offset = 0
    tempo = 1
    length = 0
    
    for line in data:
        line = line.split("#")[0].strip()
        if not line:
            continue

        t_str, cmd, args = line.strip().split(maxsplit=2)

        t = float(t_str) * tempo + (length if t_str[0] == "+" else offset)

        assert t >= length, line

        if cmd == "title":
            title = args
        elif cmd == "artist":
            artist = args
        elif cmd == "difficulty":
            difficulty = int(args)
        elif cmd == "desc":
            desc = args
        elif cmd == "audio":
            audio, url = args.split()
            if not os.path.exists(audio):
                req = requests.get(url)
                with open(audio, "wb") as file:
                    file.write(req.content)
        elif cmd == "preview":
            t0, t1 = args.split()
            preview_start = float(t0)
            preview_stop = float(t1)
        elif cmd == "tempo":
            tempo = 60 / float(args)
            offset = t
        elif cmd == "note":
            for key in args:
                notes.append(Note(t, key))

        length = t

    return Track(
        title, 
        artist,
        difficulty, 
        desc, 
        audio, 
        notes, 
        length,
        (max(0, preview_start), min(length, preview_stop)),
        wave_vis.create_vis(audio, 18),
    )

def reload_tracks(path: str = "tracks/") -> list[Track]:
    result = []
    for file_path in os.listdir(path):
        if file_path.endswith(".lkr"):
            with open(path + file_path, "r") as file:
                result.append(parse_track(file))
    return result

class NoteState(enum.Enum):
    OPEN = enum.auto()
    PERFECT = enum.auto()
    GOOD = enum.auto()
    FAILED = enum.auto()
    MISSED = enum.auto()

def draw_border(grid: dg.Grid) -> None:
    grid.clear()
    grid.chars[0, :] = ord("▀")
    grid.chars[-1, :] = ord("▄")
    grid.chars[:, 0] = ord("█")
    grid.chars[:, -1] = ord("█")