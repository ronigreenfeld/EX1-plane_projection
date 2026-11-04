# 3D Volume Plane Projection (Ex1)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Completed](https://img.shields.io/badge/Status-Completed-success.svg)]()
[![Tests: Passing](https://img.shields.io/badge/Tests-Passing%20(31%2F31)-brightgreen.svg)]()

A high-performance Object-Oriented software system for slicing and projecting arbitrary 2D planes from 3D volumetric raster data (NRRD).

*Developed as part of the **Introduction to Software Engineering (OOP/OOD)** course at Ariel University.*

---

## 📌 Overview & Scope

The system extracts arbitrary 2D cross-sectional images from a 3D volumetric raster $M$ of dimensions $sx \times sy \times sz$ (containing unsigned integer voxels of 8, 16, or 32 bits) along arbitrary user-specified spatial planes.

### Supported Planar Geometries:
* **Isosceles Triangles (3 Points):** Defined by vertices $(a, b, c)$ satisfying the tolerance condition:
  $$|dist(a,b) - dist(a,c)| < 0.001$$
* **Isosceles Trapezoids (4 Points):** Defined by coplanar vertices $(a_1, a_2, b, c)$ satisfying:
  $$|dist(a_1,b) - dist(a_2,c)| < 0.001 \quad \text{and} \quad dist(a_1, a_2) \le dist(b, c)$$

Voxel queries outside the volume boundaries are systematically assigned zero values ($v = 0$). The slicing engine is optimized for high-throughput computation, strictly exceeding the baseline requirement of **30 FPS** and targeting **100+ FPS** on standard benchmark volumes ($500^3$ voxels).

---

## 📂 Repository Layout

```text
.
├── docs/
│   ├── SRS.md                     # Software Requirements Specification (IEEE 830 style)
│   ├── DESIGN.md                  # Architectural decisions, OOP model & algorithm details
│   └── EXPERIMENTS.md             # Benchmark setup, FPS analysis & experimental results
├── src/                           # Core application source code
│   ├── engine/                    # SIMD ProjectionEngine and slicing logic
│   ├── geometry/                  # 3D spatial primitives (Point3D, Vector3D, Plane models)
│   ├── io/                        # NRRDVolume loader, CSVPlaneParser, VideoWriterService
│   └── utils/                     # Config, Logger, Exceptions hierarchy
├── data/
│   ├── real/
│   │   ├── volumes/               # Real NRRD volumetric datasets (Croissant, Head, Onion, etc.)
│   │   └── csv/                   # Cutting plane definition CSV files
│   └── synthetic/                 # Synthetic analytical volumes (sphere_100.nrrd)
├── experiments/
│   ├── outputs/                   # Generated MP4 video projections (kept locally)
│   ├── previews/                  # Representative 2D slice previews (PNG)
│   └── run_all_benchmarks.py      # Automated benchmark suite runner
├── tests/                         # Automated unit & integration test suite (31 tests)
├── Ex0.py                         # Main CLI execution entry point
├── requirements.txt               # Project dependencies
└── README.md                      # Project overview and quickstart guide
```

---

## 🚀 Quickstart & Usage

### 1. Installation & Environment Setup

```bash
# Clone repository
git clone https://github.com/<your-username>/EX1-plane_projection.git
cd EX1-plane_projection

# Initialize virtual environment
python -m venv venv

# Activate environment:
# Windows (cmd/PowerShell):
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Execution (CLI Demo Pipeline)

Execute the end-to-end projection pipeline via `Ex0.py`:
```bash
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

**Real Dataset Examples:**
```bash
# 1. Human Head MRI Scan (280 frames @ ~230 FPS)
python Ex0.py data/real/volumes/MRHead_1.nrrd data/real/csv/head.csv output_head.mp4

# 2. Large 500^3 Croissant Benchmark (100 frames @ ~75 FPS)
python Ex0.py data/real/volumes/croissant.nrrd data/real/csv/croissant.csv output_croissant.mp4

# 3. Onion Cross-Section (120 frames @ ~255 FPS)
python Ex0.py data/real/volumes/onion.nrrd data/real/csv/onion.csv output_onion.mp4
```

---

## 🧪 Testing & Verification

Run the automated test suite across all modules:
```bash
python -m unittest discover -s tests
```
*Current test suite: **31 unit and integration tests (100% Passing)** in $\approx 0.6$ seconds.*

To execute the automated multi-dataset benchmark suite:
```bash
python experiments/run_all_benchmarks.py
```

---

## 📊 Empirical Performance & Results

All benchmarks were measured on an Intel Core workstation (Windows 11, 64-bit, Python 3.12, NumPy 2.5):

| Dataset | Dimensions ($S_x \times S_y \times S_z$) | Voxel Type | Frames | Output Canvas | Average FPS | Status |
|:--- |:---:|:---:|:---:|:---:|:---:|:---:|
| **Croissant ($500^3$ Benchmark)** | $500 \times 500 \times 500$ | `uint8` | 100 | $502 \times 560$ | **73.11 FPS** | **PASSED** (2.4x minimum threshold) |
| **Human Head MRI** | $256 \times 256 \times 130$ | `int16` | 280 | $256 \times 256$ | **229.99 FPS** | **PASSED (Exceeded Target)** |
| **Onion Cross-Section** | $256 \times 256 \times 130$ | `uint8` | 120 | $256 \times 256$ | **254.48 FPS** | **PASSED (Exceeded Target)** |
| **Biscuit Cake** | $256 \times 256 \times 130$ | `uint16` | 120 | $256 \times 256$ | **252.63 FPS** | **PASSED (Exceeded Target)** |
| **Swiss Roll** | $256 \times 256 \times 130$ | `uint32` | 120 | $256 \times 256$ | **236.52 FPS** | **PASSED (Exceeded Target)** |
| **Edge Cases Suite** | $256 \times 256 \times 130$ | `int16` | 16 | $280 \times 280$ | **114.70 FPS** | **PASSED (Exceeded Target)** |

*Detailed experimental analysis, hardware profiling, and resilience logs are documented in **[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)**.*

---

## 📚 Technical Documentation

Comprehensive engineering documentation is available under [`docs/`](docs/):
* **[Software Requirements Specification (SRS)](docs/SRS.md)** – Detailed functional, non-functional, and interface requirements.
* **[Architecture & Algorithm Design](docs/DESIGN.md)** – OOD class hierarchy, scanline projection math, and vectorization design.
* **[Experiment Report](docs/EXPERIMENTS.md)** – Full evaluation methodology, hardware specifications, and benchmark output.

