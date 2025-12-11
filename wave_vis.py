import os

import numpy as np
import librosa as lb

def _analyze_audio_stream(
    y: np.ndarray[np.float32], 
    sr_in: int, 
    n_bins: int,
    n_fft: int,
    hop_length: int,
    dynamic_range_db: float
) -> tuple[np.ndarray[np.float32], np.ndarray[np.float32]]:
    """
    Internal helper function to run the STFT-to-Mel-to-Normalized-DB pipeline
    on a given audio stream.
    """
    
    # Compute "high-resolution" STFT
    S_power = np.abs(lb.stft(y, n_fft=n_fft, hop_length=hop_length))**2
    num_source_frames = S_power.shape[1]
    
    # Get the timestamps for our high-res STFT frames
    t_source = lb.frames_to_time(
        np.arange(num_source_frames),
        sr=sr_in,
        hop_length=hop_length
    )
    
    # Create and apply Mel filterbank
    mel_basis = lb.filters.mel(
        sr=sr_in, 
        n_fft=n_fft, 
        n_mels=n_bins,
        fmin=0.0,
        fmax=sr_in / 2.0
    )
    
    # mel_power has shape (n_bins, num_source_frames)
    mel_power = np.dot(mel_basis, S_power)
    
    # Convert to normalized dB
    _global_ref_power = np.max(mel_power) + 1e-6
    
    mel_db = lb.power_to_db(mel_power, ref=_global_ref_power)
    
    # normalize and clip
    normalized_db = (mel_db + dynamic_range_db) / dynamic_range_db
    normalized_db = np.clip(normalized_db, 0, 1)
    
    return normalized_db, t_source

def get_visualization_frames(
    y: np.ndarray[np.float32], 
    sr_in: int, 
    sr_out: int, 
    n_bins: int,
    n_fft: int = 2048,
    hop_length: int = -1, # Will default to n_fft // 2
    dynamic_range_db: float = 40.0,
    harmonic_preemphasis_coeff: float = 0.97,
) -> np.ndarray[np.float32]:
    """
    Computes the complete visualization sequence for a given audio waveform.
    Includes optimizations to trade precision for performance.

    Args:
        y: The audio waveform as a numpy array.
        sr_in: The sample rate of the input audio (e.g., 44100).
        sr_out: The desired output frame rate for the visualization (e.g., 60, 29.97).
        n_bins: The number of frequency bins (bars) for the visualization.
        n_fft: The size of the FFT window (affects frequency resolution).
        hop_length: The step size for the internal STFT. A smaller value
                    gives higher temporal resolution for interpolation.
                    Defaults to `n_fft // 4`.
        dynamic_range_db: The "sensitivity" of the visualizer. 
                           80.0 means bars will represent the range from -80dB to 0dB.
                           **Try 40.0 or 50.0 to reduce "noise"**
        harmonic_preemphasis_coeff: Coefficient for a pre-emphasis filter.
                                    0.97 (default) boosts high-freqs.
                                    0.0 disables.

    Returns:
        A 2D NumPy array of shape (num_frames, n_bins) where each row is a
        single visualization frame (values 0.0 to 1.0).
    """
    
    # Set hop_length for high-res STFT
    hop_length = sr_in // sr_out

    # Generate target timestamps
    duration_sec = len(y) / float(sr_in)
    num_target_frames = int(np.ceil(duration_sec * sr_out))
    
    if harmonic_preemphasis_coeff > 0.0:
        y = lb.effects.preemphasis(y, coef=harmonic_preemphasis_coeff)
    
    norm_db, t_source = _analyze_audio_stream(
        y, sr_in, n_bins, n_fft, hop_length, dynamic_range_db
    )
    
    num_source_frames = norm_db.shape[1]

    # The number of frames might be off by one due to rounding
    # We'll just truncate or pad to match num_target_frames
    n_frames_to_match = min(num_target_frames, num_source_frames)
    output_frames_raw = norm_db.T[:n_frames_to_match]
    
    # Pad if we're short (e.g., at end of audio)
    output_frames = np.zeros((num_target_frames, n_bins))
    output_frames[:n_frames_to_match] = output_frames_raw
        
    return output_frames

def create_vis(path: str, n: int = 18) -> np.ndarray[np.float32]:
    cache_path = f"vis_cache/{n}_{path.replace('/', '_').replace('.', '_')}.npy"
    if os.path.exists(cache_path):
        return np.load(cache_path)
    y, sr = lb.load(path, sr=None)
    out = get_visualization_frames(y, sr, 90, n)
    np.save(cache_path, out)
    return out


if __name__ == "__main__":
    y, sr = lb.load("audio/WAVE_(Game_Version_-_VIRTUAL_SINGER).ogg", sr=None)
    vis = get_visualization_frames(y, sr, 90, 76)
    print(vis.shape)
    breakpoint()

    # import pygame as pg
    # import display_grid as dg
    # pg.init()
    # def draw_border(grid: dg.Grid) -> None:
    #     grid.clear()
    #     grid.chars[0, :] = ord("▀")
    #     grid.chars[-1, :] = ord("▄")
    #     grid.chars[:, 0] = ord("█")
    #     grid.chars[:, -1] = ord("█")

    # class WaveVis(dg.Module):
    #     def __init__(self, parent: dg.Module, audio: str) -> None:
    #         super().__init__(parent)
            
    #         self.audio = audio
    #         y, sr = lb.load(audio, sr=None)
    #         self.vis = get_visualization_frames(y, sr, 90, 76)
    #         pg.mixer.music.load(audio)
    #         pg.mixer.music.play()

    #     def _draw(self) -> None:
    #         draw_border(self.grid)
    #         bars = self.vis[int(pg.mixer.music.get_pos() * 90 / 1000)] ** 1.5
    #         for i, bar in enumerate(bars):
    #             self.grid.chars[23 - int(bar * 22): 23, i + 2] = ord("#")

    # with dg.MainModule(mode="terminal") as main_module:
    #     vis_module = WaveVis(main_module, "audio/WAVE_(Game_Version_-_VIRTUAL_SINGER).ogg")
    #     while True:
    #         main_module.tick()
    #         main_module.draw()

