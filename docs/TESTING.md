# Test Plan & Verification Specification (TESTING)

**Course:** Introduction to Software Engineering (OOP / OOD)  
**Assignment:** Ex1 – Algorithm: Implementing a Plane Projection of 3D Volume  
**Document Version:** 1.0.0  
**Date:** November 2026  

---

## 1. Testing Philosophy & Quality Assurance Strategy

The verification strategy of the 3D Volume Plane Projection system is grounded in automated test-driven development (TDD), regression prevention, and strict compliance with the IEEE 830 specification detailed in [SRS.md](SRS.md).

### Core Testing Objectives:
1. **Mathematical Accuracy:** Every algebraic vector operation, distance metric, and scalar triple product is verified against analytical hand-calculated ground truths.
2. **Constraint Enforcement (epsilon = 0.001):** Geometric tolerances for isosceles triangle leg equality and trapezoid coplanarity are validated across valid, borderline, and violating inputs.
3. **Branchless Boundary Robustness:** Sampling points that fall partially or completely outside the 3D volume boundaries are verified to strictly return 0 without raising IndexError or degrading performance.
4. **Resilience & Fault Tolerance (FR-24 / FR-25):** The system must handle corrupted CSV syntax, non-numeric strings, and degenerate planes gracefully by logging warnings and rendering zero-filled black frames, preserving video stream continuity.
5. **Turnkey Automation:** The entire test suite executes in under 1.0 second via Python's standard `unittest` framework with zero external test runners required.

---

## 2. Automated Test Suite Architecture

The automated test suite is located under [tests/](../tests/) and comprises **31 comprehensive unit and integration tests**:

```text
tests/
├── __init__.py
├── test_geometry.py       # 11 tests: Point3D, Vector3D, Triangle & Trapezoid models
├── test_volume_io.py      # 7 tests: NRRD volume ingestion, OOB sampling, CSV parsing
├── test_slicer.py         # 6 tests: ProjectionEngine, SIMD slicing, intensity normalization
├── test_video.py          # 4 tests: VideoWriterService, even dimensions, O(1) streaming
└── test_utils.py          # 3 tests: Settings immutability, logger, custom exception hierarchy
```

### Execution Command:
```bash
python -m unittest discover -s tests
```
*Current Status: **31 Tests Passed (100% OK)** in ~0.5 seconds.*

---

## 3. Test Modules & Granular Coverage

### 3.1 3D Spatial Geometry Tests (`test_geometry.py`)
* **Vector Operations:** Tests vector magnitude (`length()`), unit normalization (`normalize()`), dot product (`dot()`), and cross product (`cross()`).
* **Operator Overloading:** Validates that `point_b - point_a` yields a `Vector3D`, `point_a + vector` yields a `Point3D`, and vector scalar multiplication/division behaves algebraically.
* **Isosceles Triangle Validation:**
  * Tests valid symmetric triangles (`|dist(a, b) - dist(a, c)| < 0.001`).
  * Tests rejection of non-isosceles triangles with `GeometryValidationError`.
  * Tests apex-to-base scanline coordinate generation across discrete rows y.
* **Isosceles Trapezoid Validation:**
  * Tests equal leg constraints (`|dist(a1, b) - dist(a2, c)| < 0.001`).
  * Tests top/bottom base width ordering (`dist(a1, a2) <= dist(b, c)`).
  * Tests 3D coplanarity using the scalar triple product (`|( (a2 - a1) x (b - a1) ) • (c - a1)| < 0.001`), strictly raising `CoplanarityError` on skew 3D quadrilaterals.

### 3.2 Volume I/O & CSV Parsing Tests (`test_volume_io.py`)
* **3D Volume Loading:** Verifies correct shape, header extraction, and unsigned integer bit-depth handling across uint8, int16, uint16, and uint32.
* **Branchless OOB Sampling:** Queries coordinates with x < 0, x >= sx, y < 0, y >= sy, z < 0, z >= sz, confirming that all out-of-bounds voxels evaluate to 0 without branching penalties.
* **CSV Parsing Flexibility:**
  * Tests pure coordinate rows (9 numbers for triangles, 12 numbers for trapezoids).
  * Tests the lecturer's format with leading count indicators (`3, x1...` and `4, x1...`) and trailing comma padding.
  * Tests comments (`#`) and empty line filtering.

### 3.3 Slicing Engine Tests (`test_slicer.py`)
* **Analytical Sphere Verification:** Slices a synthetic sphere volume at the equator (z = 50) and verifies the extracted circular cross-section matches analytical radius formulas.
* **SIMD Nearest-Neighbor Rounding:** Verifies that continuous spatial coordinates are mapped to discrete voxel indices using round-to-nearest (`np.rint`).
* **Global Normalization:** Tests that diverse voxel intensities are mapped linearly into standard uint8 display range [0, 255] using global volume bounds (v_min, v_max).
* **Degenerate Plane Fallback:** Verifies that passing an invalid plane to `slice_plane()` logs a warning and returns an all-zero matrix rather than raising an unhandled exception.

### 3.4 Video Encoding & Streaming Tests (`test_video.py`)
* **OpenCV / H.264 Even Dimensions Trap:** Verifies that odd canvas dimensions (e.g., 127 x 127) are automatically incremented by 1 (to 128 x 128) to satisfy MPEG/H.264 macroblock constraints.
* **Uniform Canvas Centering:** Tests that smaller slices are centered inside the global sequence canvas with black background padding.
* **O(1) RAM Streaming:** Verifies that sequential frames are streamed directly to disk without memory buildup.

---

## 4. Lecturer's Edge-Case Suite Breakdown (`edge_cases.csv`)

The official course dataset includes [edge_cases.csv](../data/real/csv/edge_cases.csv) testing 16 critical boundary and failure scenarios:

| Frame # | Test Category | Description / Fault Injected | Expected Behavior | Engine Result |
| :---: | :--- | :--- | :--- | :---: |
| **1** | Top Face | Normal z=139 slice through die | 120 x 120 square with single pip | **VERIFIED** |
| **2** | Bottom Face | Normal z=20 slice through die | Square cross-section with 6 pips | **VERIFIED** |
| **3** | Scientific Notation | Front face with `1.59e2` and extra spaces | Parse scientific float coordinates | **VERIFIED** |
| **4** | Oblique Plane | Plane x + y + z = 268.5 through center | Regular hexagon inscribed in triangle | **VERIFIED** |
| **5** | Corner Cut | Plane x + y + z = 408.5 cutting corner | Equilateral triangle cross-section | **VERIFIED** |
| **6** | OOB Plane | Valid triangle placed at z=300 (outside volume) | Pure black frame, zero warnings (FR-26) | **VERIFIED** |
| **7** | Asymmetric Legs | Triangle legs of 188.8 vs 226.6 | Warning issued + black frame fallback | **VERIFIED** |
| **8** | Non-Parallel Top | Trapezoid top side tilted by 16 units | Warning issued + black frame fallback | **VERIFIED** |
| **9** | Truncated Row | 4 points declared, but only 9 numbers given | CSVFormatError caught -> black frame | **VERIFIED** |
| **10** | String Token | Row contains string `"abc"` instead of float | CSVFormatError caught -> black frame | **VERIFIED** |
| **11** | Infinite Value | Row contains `"inf"` | Float error caught -> black frame | **VERIFIED** |
| **12** | Coincident Base | Triangle vertices b = c (zero width) | Degeneracy caught -> black frame | **VERIFIED** |
| **13** | Collinear Vertices | Vertices a, b, c along a straight line | Geometry error caught -> black frame | **VERIFIED** |
| **14** | Skew Quad | Vertex a2 elevated above plane of a1, b, c | CoplanarityError caught -> black frame | **VERIFIED** |
| **15** | Crossed Edges | Vertices a1 and a2 swapped (self-intersecting) | Validation caught -> black frame | **VERIFIED** |
| **16** | Oversized Base | Base width = 10,199 (> 4096 encoder limit) | Dimension limit caught -> black frame | **VERIFIED** |

All 16 frames are processed continuously at **114.70 FPS** without aborting the video generation pipeline.

---

## 5. Performance Regression Benchmarks

To guarantee compliance with Non-Functional Requirement **NFR-1** (>= 30 FPS), the test suite incorporates an automated performance benchmark executed across both analytical volumes and real medical datasets:

```bash
python experiments/run_all_benchmarks.py
```

### Regression Acceptance Criteria:
* Throughput on 500³ Croissant volume must exceed **30.0 FPS** (Measured: **73.11 FPS**).
* Throughput on standard 256³ volumes must exceed **100.0 FPS** (Measured: **230–255 FPS**).
* Total unit test suite execution time must remain under **2.0 seconds** (Measured: **~0.5 seconds**).

---

## 6. How to Run & Verify

1. **Run Full Test Suite:**
   ```bash
   python -m unittest discover -s tests
   ```

2. **Run Individual Test Modules:**
   ```bash
   python -m unittest tests.test_geometry
   python -m unittest tests.test_volume_io
   python -m unittest tests.test_slicer
   python -m unittest tests.test_video
   ```

3. **Run Multi-Dataset Benchmark Suite:**
   ```bash
   python experiments/run_all_benchmarks.py
   ```
