#!/usr/bin/env python3
"""Auto-sort RGB overlay TIFF files into tilt folders using pano_config cam_path.

Usage:
  python raw/sort_rgb_overlay_by_config.py /path/to/PANO_YYYYMMDD_HHMMSS
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path


RGB_PATTERN = re.compile(r"^RGB_(\d+)\.tiff?$", re.IGNORECASE)


def load_cam_path(config_path: Path) -> list[tuple[int, int]]:
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    cam_path = data.get("cam_path")
    if not isinstance(cam_path, list) or not cam_path:
        raise ValueError(f"Invalid or empty cam_path in {config_path}")
    parsed: list[tuple[int, int]] = []
    for item in cam_path:
        if not (isinstance(item, list) and len(item) == 2):
            raise ValueError(f"Invalid cam_path item: {item}")
        pan, tilt = int(item[0]), int(item[1])
        parsed.append((pan, tilt))
    return parsed


def find_rgb_files(rgb_dir: Path) -> list[tuple[int, Path]]:
    matches: list[tuple[int, Path]] = []
    for path in rgb_dir.rglob("*"):
        if not path.is_file():
            continue
        # Ignore files already sorted into tilt folders to keep reruns stable.
        rel_parts = path.relative_to(rgb_dir).parts
        if rel_parts and rel_parts[0].startswith("tilt_"):
            continue
        m = RGB_PATTERN.match(path.name)
        if m:
            matches.append((int(m.group(1)), path))
    if not matches:
        raise ValueError(f"No RGB_*.tif/.tiff files found under {rgb_dir}")
    matches.sort(key=lambda x: x[0])
    return matches


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python raw/sort_rgb_overlay_by_config.py /path/to/PANO_YYYYMMDD_HHMMSS"
        )

    pano_dir = Path(sys.argv[1]).expanduser().resolve()
    rgb_dir_name = "RGB_overlay"
    move_files = "--move" in sys.argv[2:]

    config_path = pano_dir / "pano_config.json"
    rgb_dir = pano_dir / rgb_dir_name

    if not pano_dir.is_dir():
        raise FileNotFoundError(f"Pano directory not found: {pano_dir}")
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    if not rgb_dir.is_dir():
        raise FileNotFoundError(f"Missing RGB directory: {rgb_dir}")

    cam_path = load_cam_path(config_path)
    rgb_files = find_rgb_files(rgb_dir)

    actual_count = len(rgb_files)
    if actual_count > len(cam_path):
        raise ValueError(
            f"Found {actual_count} RGB files, but cam_path only has {len(cam_path)} entries."
        )

    expected_per_tilt = len({pan for pan, _ in cam_path})
    used_cam_path = cam_path[:actual_count]

    tilt_counts = Counter(tilt for _, tilt in used_cam_path)

    action = shutil.move if move_files else shutil.copy2
    copied = 0

    for (rgb_idx, src), (_, tilt) in zip(rgb_files, used_cam_path):
        is_incomplete = tilt_counts[tilt] < expected_per_tilt
        tilt_folder = f"tilt_{tilt}{'_incomplete' if is_incomplete else ''}"
        dest_dir = rgb_dir / tilt_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"RGB_{rgb_idx}.tiff"
        action(str(src), str(dest))
        copied += 1

    print(f"Pano dir: {pano_dir}")
    print(f"Config entries: {len(cam_path)}")
    print(f"RGB files used: {actual_count}")
    print(f"Expected pans per tilt: {expected_per_tilt}")
    print(f"Output base: {rgb_dir}")
    print(f"Action: {'move' if move_files else 'copy'}")
    print(f"Files processed: {copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
