# 3D Volume Plane Projection (Ex1)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: In_Development](https://img.shields.io/badge/Status-In--Development-orange.svg)]()

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
│   ├── SRS.md             # Software Requirements Specification (IEEE 830 style)
│   ├── DESIGN.md          # Architectural decisions, OOP model & algorithm details
│   └── EXPERIMENTS.md     # Benchmark setup, FPS analysis & experimental results
├── src/                   # Core application source code
├── tests/                 # Automated test suite (Unit, validation & integration)
├── data/                  # Sample NRRD datasets and test CSV point configurations
├── Ex0.py                 # Main CLI demo entry point
├── requirements.txt       # Project dependencies
└── README.md              # Project overview and quickstart guide
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

**Parameters:**
* `<file.nrrd>`: Path to input 3D volumetric data file in NRRD format.
* `<file.csv>`: Path to CSV file containing 3D coordinates for consecutive planes (3 or 4 points per row).
* `<file.mp4>`: Path for the generated output video compiling consecutive plane projections.

---

## 🧪 Testing & Verification

Run the automated test suite across all modules:
```bash
python -m unittest discover -s tests
```

---

## 📊 Results & Demo Preview

> *Note: Visual artifacts and benchmark recordings will be populated upon completion of the experiment phase.*

| Volume Dimensions | Target FPS | Measured FPS | Status |
|:---:|:---:|:---:|:---:|
| $500 \times 500 \times 500$ | $\ge 100$ FPS | *TBD* | Planned |

---

## 📚 Technical Documentation

Comprehensive engineering documentation is available under [`docs/`](docs/):
* **[Software Requirements Specification (SRS)](docs/SRS.md)** – Detailed functional, non-functional, and interface requirements.
* **[Architecture & Algorithm Design](docs/DESIGN.md)** – OOD class hierarchy, scanline projection math, and vectorization design.
* **[Experiment Report](docs/EXPERIMENTS.md)** – Full evaluation methodology, hardware specifications, and benchmark output.
