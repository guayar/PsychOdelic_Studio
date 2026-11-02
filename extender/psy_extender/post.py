"""Kroki po wyniku: wyostrzanie, korekcja barw (ffmpeg), LMS (wlasna komenda). Kazdy krok z wlacznikiem."""
import shlex
import subprocess


def ffmpeg_filters(cfg):
    f = []
    if cfg["sharpen"]["enabled"]:
        amt = float(cfg["sharpen"]["amount"])
        f.append(f"unsharp=5:5:{amt}:5:5:0.0")
    c = cfg["color"]
    if c["enabled"]:
        f.append(f"eq=brightness={float(c['brightness'])}:contrast={float(c['contrast'])}"
                 f":saturation={float(c['saturation'])}:gamma={float(c['gamma'])}")
    return f


def ffmpeg_command(src, dst, cfg):
    filters = ffmpeg_filters(cfg)
    if not filters:
        return None
    return ["ffmpeg", "-y", "-i", src, "-vf", ",".join(filters), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-crf", "16", "-an", dst]


def lms_command(src, dst, cfg):
    tpl = cfg["lms"].get("command") or ""
    if not cfg["lms"]["enabled"] or not tpl:
        return None
    return shlex.split(tpl.format(**{"in": src, "out": dst}))


def run(argv, timeout=3600):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
