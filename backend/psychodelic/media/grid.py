"""Siatka klatek H3 (17n+5 przy 24 fps) i przeliczanie czasu na klatki. Czyste funkcje, bez I/O."""

FPS = 24


def snap_frames(seconds, fps=FPS):
    raw = seconds * fps
    n = max(0, round((raw - 5) / 17))
    return 17 * n + 5


def is_h3_grid(frames):
    return frames >= 5 and (frames - 5) % 17 == 0


def seconds_to_frames(seconds, fps=FPS):
    """Zaokraglenie w gore do pelnej klatki (jednoznaczna regula dla cue)."""
    import math
    return int(math.ceil(seconds * fps - 1e-9))


def frames_to_timecode(frames, fps=FPS):
    if frames < 0:
        raise ValueError("klatki ujemne")
    s, f = divmod(frames, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
