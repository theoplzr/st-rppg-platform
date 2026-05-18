#!/usr/bin/env python3
"""
Convert an AVI video into a session ZIP compatible with the Wound-rPPG app.

Expected ZIP structure:
  session_name/
    frames/
      0000.png  (or .jpg)
      0001.png
      ...
    metadata.json

Usage:
  python3 backend/scripts/avi_to_session_zip.py /path/to/video.avi
  python3 backend/scripts/avi_to_session_zip.py /path/to/video.avi --session-name pure_s01
  python3 backend/scripts/avi_to_session_zip.py /path/to/video.avi --output /path/to/pure_s01.zip
  python3 backend/scripts/avi_to_session_zip.py /path/to/video.avi --format jpg --quality 92
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cv2


def _decode_fourcc(value: float) -> str:
    code = int(value)
    chars = [chr((code >> shift) & 0xFF) for shift in (0, 8, 16, 24)]
    decoded = "".join(c for c in chars if c.isprintable() and c != "\x00")
    return decoded or "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an AVI file into a session ZIP compatible with the app.",
    )
    parser.add_argument("input_video", type=Path, help="Path to the .avi video")
    parser.add_argument(
        "--session-name",
        help="Optional session name. Defaults to the input filename stem.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output ZIP path. Defaults to ./<session-name>.zip",
    )
    parser.add_argument(
        "--format",
        choices=["png", "jpg"],
        default="png",
        help="Frame image format. Use 'jpg' for much smaller ZIPs (default: png).",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=92,
        metavar="1-100",
        help="JPEG quality when --format jpg is used (default: 92).",
    )
    return parser.parse_args()


def extract_video_to_session_dir(
    input_video: Path,
    session_name: str,
    session_root: Path,
    fmt: str = "png",
    quality: int = 92,
) -> tuple[int, dict]:
    if not input_video.exists():
        raise FileNotFoundError(f"Input video not found: {input_video}")

    capture = cv2.VideoCapture(str(input_video))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video: {input_video}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fourcc = _decode_fourcc(capture.get(cv2.CAP_PROP_FOURCC))

    session_dir = session_root / session_name
    frames_dir = session_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    timestamps_rel: list[float] = []
    frame_count = 0

    try:
        while True:
            ok, frame_bgr = capture.read()
            if not ok:
                break

            frame_path = frames_dir / f"{frame_count:04d}.{fmt}"
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality] if fmt == "jpg" else []
            if not cv2.imwrite(str(frame_path), frame_bgr, encode_params):
                raise RuntimeError(f"Unable to write frame: {frame_path}")

            if fps > 0:
                timestamps_rel.append(round(frame_count / fps, 6))
            frame_count += 1
    finally:
        capture.release()

    if frame_count == 0:
        raise RuntimeError(f"No frames extracted from video: {input_video}")

    duration_s = timestamps_rel[-1] if timestamps_rel else 0.0
    metadata = {
        "session_name": session_name,
        "date": datetime.now().isoformat(),
        "source_video": input_video.name,
        "codec": fourcc,
        "measured_fps": round(fps, 6) if fps > 0 else 0.0,
        "requested_fps": round(fps, 6) if fps > 0 else 0.0,
        "nb_frames": frame_count,
        "duration_s": round(duration_s, 6),
        "frame_width": width,
        "frame_height": height,
        "save_format": fmt,
        "timestamps_rel": timestamps_rel,
    }

    metadata_path = session_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return frame_count, metadata


def make_zip_from_session_dir(session_dir: Path, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(session_dir.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(session_dir.parent)
            zf.write(path, arcname=str(arcname))


def main() -> int:
    args = parse_args()
    input_video = args.input_video.expanduser().resolve()
    session_name = args.session_name or input_video.stem
    output_zip = (args.output or Path.cwd() / f"{session_name}.zip").expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="st_rppg_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        frame_count, metadata = extract_video_to_session_dir(
            input_video=input_video,
            session_name=session_name,
            session_root=tmp_root,
            fmt=args.format,
            quality=args.quality,
        )
        make_zip_from_session_dir(tmp_root / session_name, output_zip)

    print(f"ZIP created: {output_zip}")
    print(f"Session name: {session_name}")
    print(f"Frames: {frame_count}  format: {args.format}" + (f"  quality: {args.quality}" if args.format == "jpg" else ""))
    print(
        "Video info: "
        f"{metadata['frame_width']}x{metadata['frame_height']} @ {metadata['measured_fps']} fps",
    )
    print("Upload this ZIP from the app on the 'Session existante' tab.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
