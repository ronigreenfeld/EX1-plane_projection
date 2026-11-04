"""Automated benchmark runner for all real and synthetic datasets.

Executes two-pass plane projection on all five class volumes plus edge cases,
captures precise performance metrics, extracts representative preview slices,
and outputs a formatted Markdown summary table for docs/EXPERIMENTS.md.
"""

import os
import platform
import sys
import time
import cv2
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.engine.slicer import ProjectionEngine
from src.geometry.plane import IsoscelesTrianglePlane, IsoscelesTrapezoidPlane
from src.io.csv_parser import CSVPlaneParser
from src.io.nrrd_loader import NRRDVolume
from src.io.video_writer import VideoWriterService
from src.utils.logger import setup_logger

logger = setup_logger("benchmark_runner")


def get_hardware_info() -> dict[str, str]:
    """Retrieves hardware and environment metadata."""
    info = {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": platform.processor() or "Unknown CPU",
        "architecture": platform.machine(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "opencv": cv2.__version__,
    }
    return info


def run_single_benchmark(
    volume_path: str,
    csv_path: str,
    output_mp4_path: str,
    preview_png_path: str | None = None,
    preview_frame_idx: int = 50,
) -> dict:
    """Runs end-to-end projection benchmark on a single dataset pair."""
    logger.info("Running benchmark on volume=%s, csv=%s", volume_path, csv_path)
    
    # 1. Load Volume
    t_vol_start = time.perf_counter()
    volume = NRRDVolume.load(volume_path)
    vol_load_time = time.perf_counter() - t_vol_start
    
    # 2. Parse CSV Planes
    planes = CSVPlaneParser.parse_file(csv_path)
    
    # 3. Pass 1: Bounding Canvas calculation
    max_h, max_w = 256, 256
    for plane in planes:
        if plane.is_valid:
            h, w = plane.get_dimensions()
            if h > max_h:
                max_h = h
            if w > max_w:
                max_w = w
    canvas_h = max_h if (max_h % 2 == 0) else (max_h + 1)
    canvas_w = max_w if (max_w % 2 == 0) else (max_w + 1)

    # Global normalization intensity bounds
    v_min = float(volume.data.min())
    v_max = float(volume.data.max())

    # 4. Pass 2: Projection & Video Streaming
    engine = ProjectionEngine(volume)
    t_proj_start = time.perf_counter()
    with VideoWriterService(output_mp4_path, canvas_w, canvas_h, fps=30) as writer:
        for plane in planes:
            slice_data = engine.slice_plane(plane)
            writer.write_slice(slice_data, v_min=v_min, v_max=v_max)
    total_proj_time = time.perf_counter() - t_proj_start
    
    num_frames = len(planes)
    fps = num_frames / total_proj_time if total_proj_time > 0 else 0.0
    latency_ms = (total_proj_time / num_frames * 1000) if num_frames > 0 else 0.0
    
    # Extract representative slice preview
    if preview_png_path and os.path.exists(output_mp4_path):
        cap = cv2.VideoCapture(output_mp4_path)
        total_caps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_idx = min(preview_frame_idx, max(0, total_caps - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imwrite(preview_png_path, frame)
            logger.info("Saved preview frame %d to %s", target_idx, preview_png_path)
        cap.release()
        
    return {
        "volume_name": os.path.basename(volume_path),
        "csv_name": os.path.basename(csv_path),
        "shape": volume.shape,
        "dtype": str(volume.dtype),
        "frames": num_frames,
        "canvas_size": f"{canvas_w}x{canvas_h}",
        "total_time_sec": total_proj_time,
        "latency_ms": latency_ms,
        "fps": fps,
        "file_size_bytes": os.path.getsize(output_mp4_path) if os.path.exists(output_mp4_path) else 0,
    }


def main():
    print("=" * 80)
    print("STARTING COMPREHENSIVE EXPERIMENT BENCHMARK SUITE")
    print("=" * 80)
    
    hw = get_hardware_info()
    print(f"OS:           {hw['os']}")
    print(f"CPU:          {hw['cpu']}")
    print(f"Architecture: {hw['architecture']}")
    print(f"Python:       {hw['python']}")
    print(f"NumPy:        v{hw['numpy']}")
    print(f"OpenCV:       v{hw['opencv']}")
    print("-" * 80)

    datasets = [
        {
            "name": "Croissant (Large 500^3 Benchmark)",
            "volume": "data/real/volumes/croissant.nrrd",
            "csv": "data/real/csv/croissant.csv",
            "output": "experiments/outputs/output_croissant.mp4",
            "preview": "experiments/previews/croissant_slice.png",
            "preview_idx": 50,
        },
        {
            "name": "Human Head / Brain MRI",
            "volume": "data/real/volumes/MRHead_1.nrrd",
            "csv": "data/real/csv/head.csv",
            "output": "experiments/outputs/output_head.mp4",
            "preview": "experiments/previews/head_slice.png",
            "preview_idx": 65,
        },
        {
            "name": "Onion Cross-Section",
            "volume": "data/real/volumes/onion.nrrd",
            "csv": "data/real/csv/onion.csv",
            "output": "experiments/outputs/output_onion.mp4",
            "preview": "experiments/previews/onion_slice.png",
            "preview_idx": 60,
        },
        {
            "name": "Biscuit Cake (16-bit Unsigned)",
            "volume": "data/real/volumes/biscuit_cake.nrrd",
            "csv": "data/real/csv/biscuit_cake.csv",
            "output": "experiments/outputs/output_biscuit.mp4",
            "preview": "experiments/previews/biscuit_slice.png",
            "preview_idx": 60,
        },
        {
            "name": "Swiss Roll (32-bit Unsigned)",
            "volume": "data/real/volumes/swiss_roll.nrrd",
            "csv": "data/real/csv/swiss_roll.csv",
            "output": "experiments/outputs/output_swiss_roll.mp4",
            "preview": "experiments/previews/swiss_roll_slice.png",
            "preview_idx": 60,
        },
        {
            "name": "Edge Cases Resilience Suite",
            "volume": "data/real/volumes/MRHead_1.nrrd",
            "csv": "data/real/csv/edge_cases.csv",
            "output": "experiments/outputs/output_edge_cases.mp4",
            "preview": "experiments/previews/edge_cases_slice.png",
            "preview_idx": 5,
        },
    ]

    results = []

    for ds in datasets:
        print(f"\n>>> Processing: {ds['name']} ...")
        res = run_single_benchmark(
            volume_path=ds["volume"],
            csv_path=ds["csv"],
            output_mp4_path=ds["output"],
            preview_png_path=ds["preview"],
            preview_frame_idx=ds["preview_idx"],
        )
        res["display_name"] = ds["name"]
        results.append(res)
        print(f"    Done: {res['frames']} frames in {res['total_time_sec']:.3f}s -> {res['fps']:.2f} FPS ({res['latency_ms']:.2f} ms/frame)")

    print("\n" + "=" * 80)
    print("EXPERIMENT BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    
    header = "| Dataset | Dimensions | Voxel Dtype | Canvas (W×H) | Frames | Time (s) | Latency (ms) | FPS | SRS Target (>=30 FPS) |"
    divider = "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    print(header)
    print(divider)
    
    for r in results:
        status = "PASSED (Exceeded)" if r["fps"] >= 100 else ("PASSED" if r["fps"] >= 30 else "FAILED")
        dims = f"{r['shape'][0]}×{r['shape'][1]}×{r['shape'][2]}"
        line = (
            f"| **{r['display_name']}** | {dims} | `{r['dtype']}` | "
            f"{r['canvas_size']} | {r['frames']} | {r['total_time_sec']:.3f} | "
            f"{r['latency_ms']:.2f} ms | **{r['fps']:.2f}** | {status} |"
        )
        print(line)
        
    print("=" * 80)


if __name__ == "__main__":
    main()
