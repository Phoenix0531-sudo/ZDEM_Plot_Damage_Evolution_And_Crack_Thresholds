# ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds

**ZDEM 岩石单轴压缩渐进破裂与损伤阈值分析系统**
**Progressive Failure and Damage Threshold Analysis for ZDEM Uniaxial Compression Simulations**

| | |
|---|---|
| Maintainer | - |
| License | [MIT](LICENSE) |
| Python | >= 3.8 |
| Dependencies | numpy, scipy, matplotlib |

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Input Data Specification](#2-input-data-specification)
- [3. Algorithm and Methodology](#3-algorithm-and-methodology)
- [4. Module Reference](#4-module-reference)
- [5. Quick Start](#5-quick-start)
- [6. Output](#6-output)
- [7. Installation](#7-installation)
- [8. Project Structure](#8-project-structure)
- [9. License](#9-license)

---

## 1. Overview

This system performs automated post-processing analysis on ZDEM (Distinct Element Method) uniaxial compression simulation data. It extracts macroscopic mechanical parameters, identifies progressive failure thresholds, and generates publication-grade visualization plots.

**Key Capabilities:**

- Batch read and align 5 ZDEM monitoring data streams (_id_1.dat through _id_5.dat)
- Synthesize volumetric strain from axial and lateral components
- Extract elastic modulus (E) and Poisson's ratio (nu) via linear regression on the linear elastic segment
- Identify four progressive failure thresholds: CC, CI, CD, UCS
- Compute residual strength from post-peak stable segment
- Render a full strain-energy evolution diagram with threshold annotations
- Automatic fault tolerance and fallback mechanisms for degraded data quality

---

## 2. Input Data Specification

### 2.1 ZDEM Monitor Configuration

The following HISTORY and PROP commands must be included in the ZDEM simulation script before running this analysis system.

```bash
HIST ID 1 INTERVAL 1 , gstress group top_wall
HIST ID 2 INTERVAL 1 , gstrain group top_wall|bom_wall
PROP group p_left range x 2000.0 2100.0 y 3000.0 11000.0
PROP group p_right range x 5900.0 6000.0 y 3000.0 11000.0
HIST ID 3 INTERVAL 1 , gstrain group p_left|p_right
HIST ID 4 INTERVAL 10 , kinetic
HIST ID 5 INTERVAL 10 , step
```

### 2.2 Required Data Files

The program matches input files by the `_id_X.dat` suffix pattern. The filename prefix is arbitrary.

| ID | Physical Quantity | File Suffix | Source | Unit |
|:--:|:-----------------|:------------|:-------|:-----|
| 1 | Axial stress | `_id_1.dat` | Wall reaction force (gstress) | Pa |
| 2 | Axial strain | `_id_2.dat` | Wall vertical displacement (gstrain) | dimensionless |
| 3 | Lateral strain | `_id_3.dat` | Lateral bulging (gstrain) | dimensionless |
| 4 | Kinetic energy | `_id_4.dat` | System kinetic energy | J |
| 5 | Time step | `_id_5.dat` | Computation step counter | - |

### 2.3 Data Alignment

Time-series data from different monitors may have different recording intervals (ID 1/2/3 at INTERVAL 1, ID 4 at INTERVAL 10). The system uses numpy linear interpolation (np.interp) to map all channels onto the ID 1 (axial stress) master time axis, ensuring synchronized analysis.

---

## 3. Algorithm and Methodology

### 3.1 Volumetric Strain Synthesis

For the 2D positive-scalar convention (compaction positive, dilation negative):

    epsilon_v = epsilon_1 - epsilon_3

where epsilon_1 is axial strain and epsilon_3 is lateral strain.

### 3.2 Elastic Moduli Extraction

Elastic modulus E and Poisson's ratio nu are determined via linear regression on the linear elastic segment (30% to 50% of UCS by default).

**Robustness measures:**

1. **Primary pass**: Apply linear regression to the 30%-50% UCS interval for both E (epsilon_1 vs sigma_1) and nu (epsilon_1 vs -epsilon_3).
2. **Fallback level 1**: If the primary interval lacks sufficient variance (std(epsilon_1) < 1e-8), the search window expands to 10%-60% UCS automatically.
3. **Fallback level 2**: If the expanded window still fails, a secant modulus is computed from the interval endpoints, and Poisson's ratio defaults to 0.25.

### 3.3 Threshold Identification

| Threshold | Full Name | Detection Method |
|:----------|:----------|:-----------------|
| **UCS** | Uniaxial Compressive Strength | Global maximum of the axial stress curve |
| **CD** | Crack Damage | Maximum of volumetric strain (compression-to-dilation turning point) |
| **CI** | Crack Initiation | First point where lateral strain deviates from the Poisson baseline by more than 5 standard deviations of the elastic segment residual |
| **CC** | Crack Closure | Backward search from the elastic segment: first point where axial stress deviates from the linear elastic baseline by more than 5 standard deviations |
| **Residual** | Residual Strength | Mean of the final 10% of the post-peak stress data |

**Deviation threshold definition:**

    tol = 5 * sigma(observed - baseline)
    baseline(epsilon_1) = slope * epsilon_1 + intercept

where sigma is the standard deviation of the residual within the elastic fitting window, and the baseline function is the linear regression result extended to the full strain range.

---

## 4. Module Reference

### 4.1 `plot2D.file_io` -- Data I/O

```python
def get_file_list(DataDir: str, FileType: str) -> list[str]
def get_file_data(filename: str) -> npt.NDArray[np.float64]
def read_all_ids(DataDir: str, Thickness: float = 1.0, stress_factor: float = 1e6) -> dict[str, npt.NDArray[np.float64]]
```

**Parameters for `read_all_ids`:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `DataDir` | str | (required) | Directory containing the `_id_X.dat` files |
| `Thickness` | float | 1.0 | 2D model virtual thickness in the out-of-plane direction (m) |
| `stress_factor` | float | 1e6 | Stress scaling factor (1e6 converts Pa to MPa) |

**Returns:** Dictionary with keys `s1`, `e1`, `e3`, `ek` -- each a 1D numpy array aligned to the master time axis.

### 4.2 `plot2D.zdem_core` -- Computation Engine

```python
def analyze_progressive_failure(raw_data: dict[str, npt.NDArray[np.float64]]) -> dict[str, typing.Any]
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `raw_data` | dict | Output from `file_io.read_all_ids()` |

**Returns:** Dictionary with keys:
- `E`, `v` -- Elastic modulus and Poisson's ratio
- `UCS`, `Residual` -- Peak and residual strength (MPa)
- `CC`, `CI`, `CD` -- Crack closure, initiation, and damage stress thresholds (MPa)
- `cd_idx` -- Index of the CD point in the array
- `ev` -- Volumetric strain array

### 4.3 `plot2D.zdem_plot` -- Plotting Engine

```python
def plot_progressive_failure(raw_data, mechanics_results, output_path) -> None
```

Generates a publication-grade 4-curve (sigma_1, epsilon_3, epsilon_v, kinetic energy) evolution diagram with threshold annotations in a boxed, black-on-white style suitable for academic papers.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `raw_data` | dict | Output from `file_io.read_all_ids()` |
| `mechanics_results` | dict | Output from `zdem_core.analyze_progressive_failure()` |
| `output_path` | str | Full path for the output PNG image |

---

## 5. Quick Start

```python
import os
from plot2D import file_io, zdem_core, zdem_plot

target_dir = r"path\to\zdem\data"
thickness = 1.0
stress_factor = 1e6

raw_data = file_io.read_all_ids(target_dir, Thickness=thickness, stress_factor=stress_factor)
result = zdem_core.analyze_progressive_failure(raw_data)
zdem_plot.plot_progressive_failure(raw_data, result,
    os.path.join(target_dir, "Progressive_Failure_Evolution.png"))
```

Alternatively, use the provided entry script:

```bash
python ZDEM_main_plot_damage_and_thresholds_from_dir.py
```

Edit the path and parameter variables at the top of the script before execution.

---

## 6. Output

### 6.1 Console Report

```
=============================================
渐进破裂计算引擎已执行
弹模 E = 12345.67 MPa, 泊松比 v = 0.250
UCS = 89.12 MPa, 跌落残余 Residual = 12.34 MPa
裂纹闭合 CC = 15.67 MPa, 横向起裂 CI = 45.89 MPa, 扩容 CD = 67.01 MPa
=============================================
```

### 6.2 Figure Output

A 300 DPI PNG file containing:
- Axial stress curve (red solid line)
- Lateral strain curve (green solid line)
- Volumetric strain curve (orange solid line)
- Kinetic energy / AE proxy (gray dotted line, right y-axis)
- UCS, CC, CI, CD annotated horizontal threshold lines
- All curves plotted against axial strain on the x-axis and stress on the left y-axis

---

## 7. Installation

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Minimum Version | Purpose |
|:--------|:---------------|:--------|
| numpy | 1.21.0 | Array operations and interpolation |
| scipy | 1.7.0 | Linear regression (linregress) |
| matplotlib | 3.4.0 | Figure rendering and output |

---

## 8. Project Structure

```
ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds/
|
+-- ZDEM_main_plot_damage_and_thresholds_from_dir.py
|       Main entry script with user-configurable parameters.
|
+-- plot2D/
|   +-- __init__.py          Package metadata and version.
|   +-- file_io.py           File discovery, data reading, time-series alignment.
|   +-- zdem_core.py         Mechanical parameter extraction and threshold detection.
|   +-- zdem_plot.py         Matplotlib-based publication-grade figure generation.
|
+-- requirements.txt         Python dependency specification.
+-- setup.py                 Package installation configuration.
+-- LICENSE                  MIT license text.
+-- README.md                This document.
```

---

## 9. License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for full text.

Copyright (c) 2026
