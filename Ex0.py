#!/usr/bin/env python3
"""Main CLI entrypoint and pipeline controller for 3D Volume Plane Projection (Ex1).

Usage:
    python Ex0.py <file.nrrd> <file.csv> <file.mp4>
"""

import sys
import time
import os
import math
from src.io.nrrd_loader import NRRDVolume
from src.io.csv_parser import CSVPlaneParser
from src.io.video_writer import VideoWriterService
from src.engine.slicer import ProjectionEngine
from src.utils.config import Settings
from src.utils.exceptions import ProjectionError
from src.utils.logger import setup_logger

logger = setup_logger("Ex0_main")


def print_progress_bar(iteration: int, total: int, current_fps: float, bar_length: int = 30) -> None:
    """Renders a dynamic visual progress bar in the terminal (SRS FR-6)."""
    percent = (iteration / total) * 100.0 if total > 0 else 100.0
    filled = int(bar_length * iteration // total) if total > 0 else bar_length
    bar = "=" * filled + (">" if filled < bar_length else "") + " " * (bar_length - filled - (1 if filled < bar_length else 0))
    sys.stdout.write(f"\rProgress: [{bar}] {iteration}/{total} ({percent:.1f}%) | {current_fps:.1f} FPS")
    sys.stdout.flush()


def run_pipeline(nrrd_path: str, csv_path: str, output_mp4: str) -> None:
    """Executes the two-pass slicing and video encoding pipeline."""
    print("=" * 70)
    print("3D Volume Plane Projection Pipeline (Ex1)")
    print("=" * 70)

    # 1. Volume Ingestion
    print(f"[*] Ingesting 3D volume from: '{nrrd_path}'...")
    volume = NRRDVolume.load(nrrd_path)
    sx, sy, sz = volume.shape
    print(f"    -> Volume Dimensions: {sx} x {sy} x {sz} voxels")
    print(f"    -> Voxel Data Type:   {volume.dtype}")

    # 2. Pass 1: Global Geometry Inspection & Canvas Sizing
    print(f"[*] [Pass 1/2] Parsing cutting planes from: '{csv_path}'...")
    planes = CSVPlaneParser.parse_file(csv_path)
    total_planes = len(planes)
    if total_planes == 0:
        raise ProjectionError(f"No cutting plane definitions found in '{csv_path}'.")

    print(f"    -> Parsed {total_planes} cutting plane specifications.")

    # Calculate global maximum bounding box across all valid geometries
    max_h = 256
    max_w = 256
    valid_count = 0
    for p in planes:
        if p.is_valid:
            valid_count += 1
            h, w = p.get_dimensions()
            if h > max_h:
                max_h = h
            if w > max_w:
                max_w = w

    # Enforce Even Dimensions (H.264 / OpenCV constraint)
    canvas_h = max_h if (max_h % 2 == 0) else (max_h + 1)
    canvas_w = max_w if (max_w % 2 == 0) else (max_w + 1)

    print(f"    -> Valid Geometries:  {valid_count}/{total_planes} planes")
    print(f"    -> Uniform Canvas:    {canvas_w} x {canvas_h} pixels (Even Dimensions Enforced)")

    # 3. Pass 2: High-Speed Streaming Slicing & Video Encoding
    print(f"[*] [Pass 2/2] Slicing planes and streaming to: '{output_mp4}'...")
    engine = ProjectionEngine(volume)

    # Global normalization intensity bounds
    v_min = float(volume.data.min())
    v_max = float(volume.data.max())

    start_time = time.perf_counter()

    with VideoWriterService(
        output_path=output_mp4,
        canvas_width=canvas_w,
        canvas_height=canvas_h,
        fps=Settings.DEFAULT_VIDEO_FPS
    ) as video_writer:

        for idx, plane in enumerate(planes, start=1):
            slice_frame = engine.slice_plane(plane)
            video_writer.write_slice(slice_frame, v_min=v_min, v_max=v_max)

            # Update progress bar every frame or every 5 frames
            elapsed_so_far = time.perf_counter() - start_time
            current_fps = (idx / elapsed_so_far) if elapsed_so_far > 0 else 0.0
            print_progress_bar(idx, total_planes, current_fps)

    total_elapsed = time.perf_counter() - start_time
    avg_fps = (total_planes / total_elapsed) if total_elapsed > 0 else 0.0

    sys.stdout.write("\n")  # New line after progress bar

    # 4. Performance Summary Report (SRS FR-6 & NFR-1)
    print("\n" + "=" * 70)
    print("Execution & Benchmark Performance Summary")
    print("=" * 70)
    print(f"  * Total Processed Frames: {total_planes} frames")
    print(f"  * Total Processing Time:  {total_elapsed:.4f} seconds ({total_elapsed*1000/total_planes:.2f} ms/frame)")
    print(f"  * Average Computation FPS: {avg_fps:.2f} FPS")

    # Evaluate compliance against assignment NFR
    if avg_fps >= Settings.TARGET_EXPECTED_FPS:
        perf_status = f"[EXCELLENT] Exceeded expected target ({Settings.TARGET_EXPECTED_FPS} FPS)"
    elif avg_fps >= Settings.TARGET_MIN_FPS:
        perf_status = f"[PASS] Met minimum threshold (>= {Settings.TARGET_MIN_FPS} FPS)"
    else:
        perf_status = f"[WARNING] Below minimum requirement ({Settings.TARGET_MIN_FPS} FPS)"

    print(f"  * Performance Compliance:  {perf_status}")
    print(f"  * Generated Video File:   {output_mp4} ({os.path.getsize(output_mp4)} bytes)")
    print("=" * 70)


def main() -> int:
    """CLI argument validation and entrypoint execution."""
    if len(sys.argv) != 4:
        print("Usage Error: Exactly 3 arguments required.", file=sys.stderr)
        print("Syntax: python Ex0.py <file.nrrd> <file.csv> <file.mp4>", file=sys.stderr)
        return 1

    nrrd_file = sys.argv[1]
    csv_file = sys.argv[2]
    mp4_file = sys.argv[3]

    try:
        run_pipeline(nrrd_file, csv_file, mp4_file)
        return 0
    except ProjectionError as err:
        logger.error("Projection pipeline failed with domain error: %s", err)
        print(f"\n[ERROR] Pipeline failed: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        logger.exception("Unexpected error encountered during execution: %s", err)
        print(f"\n[UNEXPECTED ERROR] {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
