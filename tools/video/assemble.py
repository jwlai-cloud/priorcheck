# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cut the recording to the narration and mux it.

The capture logged when each beat actually happened; the audio files know how
long each beat speaks for. Where the picture ran longer than the voice — the
agent run is the big one — the video is sped up for that stretch only, so the
wait still reads as a wait without eating a third of the runtime.

    uv run python tools/video/assemble.py
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
CAP = HERE / "capture"
AUDIO = HERE / "audio"
OUT = HERE / "sceneroom-demo.mp4"

TARGET = 174.0  # seconds; leaves headroom under a 3:00 cap


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        print(" ".join(cmd[:6]), "...")
        print(proc.stderr[-1500:])
        raise SystemExit(f"ffmpeg failed ({proc.returncode})")


def probe(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> int:
    timings = json.loads((CAP / "timings.json").read_text())
    lengths = {m["id"]: m["seconds"] for m in json.loads((AUDIO / "manifest.json").read_text())}
    src = CAP / "screen.webm"
    if not src.exists():
        sys.exit("no capture — run capture.py first")

    work = CAP / "segments"
    work.mkdir(exist_ok=True)

    # One segment per beat, each retimed to its narration length. A beat whose
    # picture ran long is sped up; one that ran short is slowed. Either way the
    # segment ends up exactly as long as the voice that goes over it.
    segments: list[pathlib.Path] = []
    plan: list[tuple[str, float, float, float]] = []
    for beat in timings["beats"]:
        vid_len = beat["end"] - beat["start"]
        want = lengths.get(beat["id"], vid_len)
        speed = max(0.5, min(6.0, vid_len / want))  # setpts factor
        seg = work / f"{beat['id']}.mp4"
        run([
            "ffmpeg", "-y", "-v", "error",
            "-ss", str(beat["start"]), "-t", str(vid_len), "-i", str(src),
            "-vf", f"setpts=PTS/{speed},fps=30,scale=1440:-2",
            "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", str(seg),
        ])
        segments.append(seg)
        plan.append((beat["id"], vid_len, want, speed))
        print(f"  {beat['id']:<14} {vid_len:6.1f}s → {want:5.1f}s  ×{speed:.2f}")

    concat = work / "list.txt"
    concat.write_text("".join(f"file '{s.name}'\n" for s in segments))
    silent = CAP / "silent.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat), "-c", "copy", str(silent)])

    # The narration, in beat order, end to end. It lines up because every
    # segment was cut to its own beat's length.
    alist = work / "audio.txt"
    alist.write_text("".join(f"file '{(AUDIO / (b['id'] + '.mp3')).resolve()}'\n"
                             for b in timings["beats"]))
    voice = CAP / "voice.mp3"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(alist), "-c", "copy", str(voice)])

    vlen, alen = probe(silent), probe(voice)
    print(f"\npicture {vlen:.1f}s · voice {alen:.1f}s")

    # Trim the whole thing to the budget if it is still long.
    tempo = max(1.0, alen / TARGET)
    afilter = f"atempo={tempo:.4f}" if tempo > 1.001 else "anull"
    vfilter = f"setpts=PTS/{tempo:.4f}" if tempo > 1.001 else "null"
    if tempo > 1.001:
        print(f"over budget — tightening everything by ×{tempo:.3f}")

    run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(silent), "-i", str(voice),
        "-filter:v", vfilter, "-filter:a", afilter,
        "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(OUT),
    ])
    final = probe(OUT)
    print(f"\n{OUT}  —  {int(final // 60)}:{final % 60:04.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
