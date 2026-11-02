"""Model osi montazowej: klipy z zakresami zrodla [in, out) i pozycja na osi w klatkach (FPS timeline).

Zasady: out jest WYLACZNY; klipy na osi nie moga sie nakladac; master audio to osobna sciezka
(nie jest tu zmieniana). Eksport: JSON i CSV (EDL opcjonalnie nie jest robione).
"""
import csv
import io
import json
from dataclasses import dataclass, asdict

from .grid import frames_to_timecode


class TimelineError(ValueError):
    pass


@dataclass
class Clip:
    clip_id: str
    source_path: str           # wzgledna nazwa artefaktu w projekcie
    source_in: int             # klatka zrodla, wlacznie
    source_out: int            # klatka zrodla, WYLACZNIE
    timeline_start: int        # klatka na osi montazowej

    @property
    def length(self):
        return self.source_out - self.source_in

    @property
    def timeline_end(self):
        return self.timeline_start + self.length


def validate(clips):
    errors = []
    ids = set()
    for c in clips:
        if c.clip_id in ids:
            errors.append(f"zduplikowany id: {c.clip_id}")
        ids.add(c.clip_id)
        if c.source_out <= c.source_in:
            errors.append(f"{c.clip_id}: out musi byc > in (out wylaczne)")
        if c.source_in < 0 or c.timeline_start < 0:
            errors.append(f"{c.clip_id}: wartosci ujemne")
    ordered = sorted(clips, key=lambda c: c.timeline_start)
    for a, b in zip(ordered, ordered[1:]):
        if b.timeline_start < a.timeline_end:
            errors.append(f"{a.clip_id} i {b.clip_id} nakladaja sie na osi")
    return errors


def export_json(clips, fps=24):
    errs = validate(clips)
    if errs:
        raise TimelineError("; ".join(errs))
    items = [dict(asdict(c), timeline_start_tc=frames_to_timecode(c.timeline_start, fps),
                  duration_frames=c.length) for c in sorted(clips, key=lambda c: c.timeline_start)]
    return json.dumps({"fps": fps, "items": items}, ensure_ascii=False, indent=2)


def export_csv(clips, fps=24):
    errs = validate(clips)
    if errs:
        raise TimelineError("; ".join(errs))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["clip_id", "source_path", "source_in", "source_out", "timeline_start", "timeline_start_tc", "frames"])
    for c in sorted(clips, key=lambda c: c.timeline_start):
        w.writerow([c.clip_id, c.source_path, c.source_in, c.source_out, c.timeline_start,
                    frames_to_timecode(c.timeline_start, fps), c.length])
    return buf.getvalue()
