# Software Requirements Specification (SRS)

## Project: 3D Volume Plane Projection (Ex1)

### 1. Introduction

#### 1.1 Purpose
This document specifies the functional and non-functional requirements for the **3D Volume Plane Projection Engine**. The software extracts arbitrary 2D cross-sectional images from 3D volumetric datasets and compiles them into a video sequence.

#### 1.2 Scope
The system ingests 3D volumetric raster data in **NRRD** format and a sequence of plane definitions from a CSV file. It samples and projects the corresponding 2D slices from the 3D volume, mapping 3D voxel intensities to 2D image pixels, and outputs an **MP4** video compiling the resulting frames.

#### 1.3 Definitions, Acronyms, and Abbreviations
* **NRRD:** Nearly Raw Raster Data (standard volumetric format).
* **Voxel (Volume Element):** Discrete 3D sample point in the source volume $M$.
* **Pixel (Picture Element):** Discrete 2D element in the output matrix $E$.
* **FPS:** Frames Per Second (throughput metric for plane projection).
* **OOB:** Out of Bounds (coordinates falling outside the dimensions of volume $M$).
* **EPS:** Epsilon tolerance ($\epsilon = 0.001$) for geometric equality validation.

---

### 2. Problem Definition & Core Challenges

The problem requires translating continuous spatial plane definitions into discrete digital images while addressing three key technical challenges:
1. **Continuous-to-Discrete Mapping:** Continuous spatial points must be mapped to discrete integer indices efficiently (nearest-neighbor sampling).
2. **Boundary Padding:** Any sample point extending beyond the finite dimensions of the matrix must default to value 0 without performance-heavy branching.
3. **Aspect Ratio Preservation:** Variable-width scanlines must be horizontally centered inside a rectangular output matrix to preserve accurate geometry.

---

### 3. Functional Requirements (FR)

* **FR-1: Volume Ingestion & File I/O**
  * The system shall load 3D raster arrays from valid NRRD files.
  * Matrix dimensions $sx \times sy \times sz$ satisfy $1 \le sx, sy, sz < 2^{10}$.
  * Voxel entries are unsigned integers of 8, 16, or 32 bits.
  * The system must verify the input is strictly 3D, explicitly rejecting 2D or 4D NRRD files.
  * File I/O errors (e.g., missing files, corrupted headers, or lack of write permissions for the MP4) shall be handled gracefully with informative user prompts instead of hard crashes.

* **FR-2: Coordinate Parsing & Input Validation**
  * The system shall parse a CSV file where each row defines a single cutting plane:
    * **9 numeric values:** Interpreted as 3 points $(a, b, c)$.
    * **12 numeric values:** Interpreted as 4 points $(a_1, a_2, b, c)$.
  * The system shall validate geometric constraints using tolerance $\epsilon = 0.001$:
    * **Isosceles Triangle (3 points):** $|\text{dist}(a, b) - \text{dist}(a, c)| < \text{EPS}$.
    * **Isosceles Trapezoid (4 points):** $|\text{dist}(a_1, b) - \text{dist}(a_2, c)| < \text{EPS}$ and $\text{dist}(a_1, a_2) \le \text{dist}(b, c)$.
    * **Coplanarity:** For 4 points, coplanarity shall be strictly validated via the scalar triple product: $|(\vec{a_1 a_2} \times \vec{a_1 b}) \cdot \vec{a_1 c}| < \text{EPS}$.
  * Degenerate geometries (e.g., zero-length edges or collinear points) and invalid planes shall generate an empty black frame (zero-filled matrix) to preserve video-frame synchronization, with an appropriate warning logged.

* **FR-3: Planar Slicing Algorithm**
  * **Geometry Dimensions:**
    * **Isosceles Triangle $(a, b, c)$:** $D_{height} = \lceil \text{dist}(a, b) \rceil$ and $D_{width} = \lceil \text{dist}(b, c) \rceil$. Scanline boundary markers initialize at the apex: $a_1 = a$, $a_2 = a$.
    * **Isosceles Trapezoid $(a_1, a_2, b, c)$:** $D_{height} = \lceil \text{dist}(a_1, b) \rceil = \lceil \text{dist}(a_2, c) \rceil$ and $D_{width} = \lceil \text{dist}(b, c) \rceil$. Scanline boundary markers initialize at the top base: $a_1 = a_1$, $a_2 = a_2$.
  * Output matrix $E$ is initialized with dimensions $[D_{height} \times D_{width}]$.
  * For each scanline step $y \in [0, D_{height} - 1]$, the scanline width $d_{12}$ and spatial step vector $\hat{d}_p$ are computed along the interpolated endpoints $a_1, a_2$.
  * Horizontal scan ($x$-axis): Voxels are sampled from $M$, horizontally centered via $x = \lfloor (D_{width}/2) - (d_{12}/2) \rfloor + x_1$, and mapped into $E[y, x]$.

* **FR-4: Out-of-Bounds (OOB) Handling**
  * For any sampling coordinate $p(x, y, z)$, if $x < 0 \lor x \ge sx \lor y < 0 \lor y \ge sy \lor z < 0 \lor z \ge sz$, the sampled value defaults to 0.

* **FR-5: Video Encoding & Intensity Scaling**
  * **Intensity Normalization:** Voxel values (including 16-bit and 32-bit types) shall be scaled/normalized linearly to standard 8-bit unsigned integers (`uint8`, $[0, 255]$) for valid video display.
  * **Even Dimensions Constraint (H.264 / OpenCV Trap):** Video codecs (such as H.264/MP4) require frame width and height to be strictly even integers (multiples of 2) due to macroblock compression (YUV420p subsampling). If any dimension is odd, it shall be padded (zero-padded on the right/bottom) to the nearest even number to prevent silent `cv2.VideoWriter` initialization failure or corrupt media output.
  * **Uniform Canvas Synchronization:** All frames written into a single MP4 container stream must possess identical canvas dimensions. In cases where consecutive planes have varying dimensions, each frame shall be centered on a unified canvas sized to the maximum required dimensions across the sequence.
  * **Video Container:** The system shall assemble all sequential 2D projection matrices into an MP4 container (H.264 / mp4v codec) at a standard playback rate (default: 30 FPS).
  * **Memory Streaming:** Frames shall be streamed directly into the video writer sequentially to avoid accumulating uncompressed frames in memory.

* **FR-6: CLI UX & Logging**
  * **Execution Signature:** The system must strictly expose and adhere to the command-line interface contract specified in the project requirements:
    ```bash
    python Ex0.py <file.nrrd> <file.csv> <file.mp4>
    ```
    Where:
    * `<file.nrrd>`: Positional argument 1 — path to existing, valid 3D NRRD file.
    * `<file.csv>`: Positional argument 2 — path to existing CSV containing plane definitions.
    * `<file.mp4>`: Positional argument 3 — destination path for the generated MP4 file.
  * **Progress Bar:** A visual progress indicator shall be displayed in the terminal during the extraction and encoding phases.
  * **Performance Summary:** Upon completion, the system shall print a summary detailing the number of processed frames, total execution time, and average computation FPS.
  * **Logging:** Computational and validation errors shall be written to a dedicated log file (`project.log`) rather than cluttering standard output.

---

### 4. Non-Functional Requirements (NFR)

* **NFR-1: Performance Throughput**
  * On a volume of $500^3$ voxels: **Minimum Threshold:** $\ge 30$ FPS | **Target Throughput:** $\ge 100$ FPS.
  * Inner sampling loops must utilize vectorized array operations (NumPy) to minimize execution overhead.

* **NFR-2: Memory Management**
  * The volumetric matrix $M$ shall be loaded once and accessed via shared memory views across all slicing operations.

* **NFR-3: Architecture**
  * The system shall follow a modular design, separating I/O operations, geometric logic, algorithmic slicing, and video encoding into distinct, independent classes following SOLID principles.

---

### 5. Verification & Testing Strategy

1. **Unit Testing:** Verification of Euclidean distance calculations, vector normalization, coplanarity checks, and $\epsilon$-tolerance validation.
2. **Input Validation:** Correct parsing of CSV rows, File I/O error handling, and degenerate geometry resilience.
3. **Boundary Testing:** Verification that planes positioned strictly outside volume boundaries produce zero-filled arrays.
4. **Synthetic Volume Verification:** Extracting a planar slice through a mathematically generated 3D sphere to verify accurate analytical circular outputs.
5. **Performance Benchmark:** Measuring the total execution time of consecutive plane extractions using `time.perf_counter()` to validate compliance with the 30+ / 100+ FPS requirement.
