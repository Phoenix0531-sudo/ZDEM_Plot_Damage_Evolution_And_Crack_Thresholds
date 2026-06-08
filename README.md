<div align="center">

# ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds

**ZDEM 岩石单轴压缩渐进破裂与损伤阈值分析系统**
**Progressive Failure and Damage Threshold Analysis for ZDEM Uniaxial Compression Simulations**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](setup.py)
[![Dependencies](https://img.shields.io/badge/dependencies-numpy%20%7C%20scipy%20%7C%20matplotlib-lightgrey)](requirements.txt)

</div>

---

## 项目简介 | Overview

在 ZDEM 离散元单轴压缩模拟中，微观监测数据（应力、应变、动能）以多个独立的时间序列文件输出，手动提取力学参数和破裂阈值不仅繁琐，且难以保证一致性和可复现性。本系统提供了端到端的自动化解决方案。

> In ZDEM uniaxial compression simulations, microscopic monitoring data (stress, strain, kinetic energy) are exported as multiple independent time-series files. Manually extracting mechanical parameters and failure thresholds is tedious and prone to inconsistency. This system provides an end-to-end automated solution.

**技术特性 | Technical Highlights**

| 特性 | Feature | 说明 |
|------|---------|------|
| **多源数据自动对齐** | Multi-source auto-alignment | 基于 numpy 线性插值，将不同采样频率的监测流同步至全局主轴 |
| **三级弹性参数容错** | 3-level elastic fallback | 从标准 30%-50% UCS 区间到割线模量，逐级降级确保零崩溃输出 |
| **5-sigma 阈值检测** | 5-sigma threshold detection | 基于弹性段残差标准差的自适应阈值，无需人工调参 |
| **顶刊级纯黑白图表** | Publication-grade B/W figure | 封闭边框、刻度向内、四曲线叠加，符合岩土顶刊排版规范 |
| **免调参全自动流水线** | Zero-parameter pipeline | 数据读入 -> 参数提取 -> 阈值识别 -> 图表渲染，一键完成 |

---

## 目录 | Table of Contents

- [数据准备 | Data Preparation](#数据准备--data-preparation)
- [算法原理 | Algorithm](#算法原理--algorithm)
- [模块文档 | Module Reference](#模块文档--module-reference)
- [快速开始 | Quick Start](#快速开始--quick-start)
- [输出说明 | Output](#输出说明--output)
- [安装依赖 | Installation](#安装依赖--installation)
- [项目结构 | Project Structure](#项目结构--project-structure)
- [引用 | Citation](#引用--citation)
- [许可证 | License](#许可证--license)

---

## 数据准备 | Data Preparation

在运行分析前，须在 ZDEM 脚本中配置以下监测指令，以导出五个必需的 .dat 文件。

> The following HISTORY and PROP commands must be included in the ZDEM simulation script to export the five required .dat files.

```bash
HIST ID 1 INTERVAL 1 , gstress group top_wall
HIST ID 2 INTERVAL 1 , gstrain group top_wall|bom_wall
PROP group p_left range x 2000.0 2100.0 y 3000.0 11000.0
PROP group p_right range x 5900.0 6000.0 y 3000.0 11000.0
HIST ID 3 INTERVAL 1 , gstrain group p_left|p_right
HIST ID 4 INTERVAL 10 , kinetic
HIST ID 5 INTERVAL 10 , step
```

### 数据文件规格 | Data File Specification

系统按 `_id_X.dat` 后缀自动匹配文件，不限制文件名前缀长度。

> Files are matched by the `_id_X.dat` suffix; the filename prefix is arbitrary.

| ID | 物理量 | Quantity | 文件后缀 | 来源 | 单位 |
|:--:|:-------|:---------|:---------|:-----|:-----|
| 1 | 轴向应力 | Axial stress | `_id_1.dat` | 顶底墙支座反力 (gstress) | Pa |
| 2 | 轴向应变 | Axial strain | `_id_2.dat` | 顶底墙垂向位移 (gstrain) | - |
| 3 | 横向应变 | Lateral strain | `_id_3.dat` | 左右组水平位移差 (gstrain) | - |
| 4 | 动能 | Kinetic energy | `_id_4.dat` | 体系总动能（AE 代理） | J |
| 5 | 计算步 | Time step | `_id_5.dat` | 累计计算步数 | - |

### 数据对齐机制 | Data Alignment

ID 1/2/3 以 INTERVAL 1 记录，ID 4 以 INTERVAL 10 记录。系统以 ID 1 的时间轴为主轴，通过 `numpy.interp` 线性插值将所有通道映射至统一时间基底，保证各序列严格同步。

> ID 1/2/3 are recorded at INTERVAL 1 while ID 4 is at INTERVAL 10. The system uses `numpy.interp` to map all channels onto the ID 1 master time axis, ensuring strict synchronization.

---

## 算法原理 | Algorithm

### 体应变合成 | Volumetric Strain

采用二维全正标量约定（压缩为正、膨胀为负），体积应变由轴向应变与横向应变合成。

> Using the 2D positive-scalar convention (compaction positive, dilation negative), volumetric strain is synthesized from axial and lateral components.

```
epsilon_v = epsilon_1 - epsilon_3
```

### 弹性参数提取 | Elastic Moduli

弹性模量 E 与泊松比 nu 通过对线弹性段进行线性回归得到。系统内置三级容错机制以应对数据质量退化。

> Elastic modulus E and Poisson's ratio nu are obtained via linear regression on the linear elastic segment. A 3-level fallback mechanism handles data quality degradation.

| 级别 | Level | 区间 | 方法 |
|:----:|:------|:-----|:-----|
| 1 | Primary | 30%-50% UCS | 标准线性回归 |
| 2 | Fallback | 10%-60% UCS | 方差不足时自动扩窗 |
| 3 | Emergency | 全区间端点 | 割线模量，泊松比默认 0.25 |

### 阈值识别 | Threshold Identification

| 阈值 | Threshold | 识别方法 |
|:-----|:----------|:---------|
| **UCS** | 单轴抗压强度 | 轴向应力全局最大值 |
| **CD** | 扩容损伤点 | 体应变极大值（压缩转膨胀拐点） |
| **CI** | 微裂缝起裂点 | 侧应变首次偏离泊松基线超过 5-sigma |
| **CC** | 微裂缝闭合点 | 反向搜索：轴向应力首次偏离弹性基线超过 5-sigma |
| **Residual** | 残余强度 | 峰后末段 10% 数据均值 |

偏差阈值定义为弹性拟合窗口残差标准差的 5 倍，基线为线性回归结果向全应变范围的延伸。

> The deviation threshold is defined as 5 times the standard deviation of the elastic fitting window residual. The baseline is the linear regression result extended to the full strain range.

```
tol = 5 * sigma(observed - baseline)
baseline(epsilon_1) = slope * epsilon_1 + intercept
```

---

## 模块文档 | Module Reference

### `plot2D.file_io` -- 数据 I/O 模块

```python
def get_file_list(DataDir: str, FileType: str) -> list[str]
def get_file_data(filename: str) -> npt.NDArray[np.float64]
def read_all_ids(DataDir: str, Thickness: float = 1.0, stress_factor: float = 1e6) -> dict
```

| 参数 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| `DataDir` | str | 必填 | 包含 `_id_X.dat` 文件的目录 |
| `Thickness` | float | 1.0 | 2D 模型法向虚拟厚度 (m) |
| `stress_factor` | float | 1e6 | 应力缩放因子 (Pa -> MPa) |

**返回:** 字典 `{s1, e1, e3, ek}`，各值为对齐至主时间轴的一维 numpy 数组。

### `plot2D.zdem_core` -- 计算引擎

```python
def analyze_progressive_failure(raw_data: dict) -> dict
```

| 参数 | 类型 | 说明 |
|:-----|:-----|:-----|
| `raw_data` | dict | `file_io.read_all_ids()` 的返回值 |

**返回:** 含 `E`, `v`, `UCS`, `Residual`, `CC`, `CI`, `CD`, `cd_idx`, `ev` 的字典。

### `plot2D.zdem_plot` -- 渲染引擎

```python
def plot_progressive_failure(raw_data, mechanics_results, output_path) -> None
```

生成 300 DPI 黑白线型 PNG 图表，包含应力-应变-动能四条曲线及阈值标注线。

| 参数 | 类型 | 说明 |
|:-----|:-----|:-----|
| `raw_data` | dict | `file_io.read_all_ids()` 的返回值 |
| `mechanics_results` | dict | `zdem_core.analyze_progressive_failure()` 的返回值 |
| `output_path` | str | PNG 输出路径 |

---

## 快速开始 | Quick Start

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

也可直接运行入口脚本（使用前修改脚本顶部的路径与参数）。

> Alternatively, use the provided entry script (edit path and parameters at the top before execution).

```bash
python ZDEM_main_plot_damage_and_thresholds_from_dir.py
```

---

## 输出说明 | Output

### 控制台报告 | Console Report

```
=============================================
渐进破裂计算引擎已执行
弹模 E = 12345.67 MPa, 泊松比 v = 0.250
UCS = 89.12 MPa, 跌落残余 Residual = 12.34 MPa
裂纹闭合 CC = 15.67 MPa, 横向起裂 CI = 45.89 MPa, 扩容 CD = 67.01 MPa
=============================================
```

### 图表输出 | Figure Output

- 轴向应力曲线（红色实线）
- 横向应变曲线（绿色实线）
- 体积应变曲线（橙色实线）
- 动能/声发射代理（灰色点线，右侧纵轴）
- UCS / CC / CI / CD 水平阈值标注线
- 300 DPI 封闭边框格式，适合学术论文直接使用

---

## 安装依赖 | Installation

```bash
pip install -r requirements.txt
```

| 包 | 最低版本 | 用途 |
|:---|:---------|:-----|
| numpy | 1.21.0 | 数组运算与插值 |
| scipy | 1.7.0 | 线性回归分析 |
| matplotlib | 3.4.0 | 图表渲染输出 |

---

## 项目结构 | Project Structure

```
ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds/
|
+-- ZDEM_main_plot_damage_and_thresholds_from_dir.py
|       主入口脚本（可配置参数）
|
+-- plot2D/
|   +-- __init__.py          包元数据与版本号
|   +-- file_io.py           文件发现、数据读取、时序对齐
|   +-- zdem_core.py         力学参数提取与破裂阈值检测
|   +-- zdem_plot.py         基于 matplotlib 的学术图表渲染
|
+-- requirements.txt         Python 依赖声明
+-- setup.py                 包安装配置
+-- LICENSE                  开源许可
+-- README.md                本文档
```

---

## 引用 | Citation

If you use this software in your research, please cite it as:

```bibtex
@software{zdem_damage_evolution2026,
  title     = {{ZDEM} Progressive Failure and Damage Threshold Analysis System},
  year      = {2026},
  url       = {https://github.com/Phoenix0531-sudo/ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds},
  license   = {MIT}
}
```

---

## 许可证 | License

This project is open-sourced under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Made for the ZDEM research community**

</div>
