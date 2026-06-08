# ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds

**渐进破裂与损伤阈值分析系统 / Progressive Failure & Damage Threshold Analysis System**

> **维护人 / Maintainer**: 包羡钧 (Bao Xianjun)

---

## 项目简介 / Introduction

这是一套面向 ZDEM（离散元法）岩石单轴压缩模拟数据的后处理分析系统。  
This is a post-processing analysis system for ZDEM (Distinct Element Method) uniaxial compression simulation data.

它能从微观监测数据中自动提取宏观力学参数与渐进破裂阈值，并生成顶刊级别的全演化破裂图表。  
It automatically extracts macroscopic mechanical parameters and progressive failure thresholds from microscopic monitoring data, producing publication-ready evolution plots.

**核心能力 / Core Capabilities**:

- 批量读取 5 类 ZDEM 微观监测文件 (_id_1.dat ~ _id_5.dat) / Batch reading of 5 ZDEM monitoring files
- 自动化合成体积应变 / Automatic volumetric strain synthesis
- 提取弹性模量 E、泊松比 ν / Elastic modulus & Poisson's ratio extraction
- 识别四大破裂阈值：CC、CI、CD、UCS / Identification of 4 failure thresholds: CC, CI, CD, UCS
- 输出学术级全应变-能量演化折线图 / Academic-grade full strain-energy evolution plots

---

## 数据准备 / Data Preparation

在运行本分析系统之前，需在 ZDEM 脚本中包含以下监测指令，以导出必要的 `.dat` 文件。  
Before running this system, ensure your ZDEM simulation script includes the following monitoring commands to export the required `.dat` files.

```bash
# 轴向应力监测（hist*_id_1.dat）/ axial stress
HIST ID 1 INTERVAL 1 , gstress group top_wall
# 轴向应变监测（hist*_id_2.dat）/ axial strain
HIST ID 2 INTERVAL 1 , gstrain group top_wall|bom_wall
# 框选试件左侧边缘 / left edge group
PROP group p_left range x 2000.0 2100.0 y 3000.0 11000.0
# 框选试件右侧边缘 / right edge group
PROP group p_right range x 5900.0 6000.0 y 3000.0 11000.0
# 横向应变监测（hist*_id_3.dat）/ lateral strain
HIST ID 3 INTERVAL 1 , gstrain group p_left|p_right
# 体系动能监测（hist*_id_4.dat）/ kinetic energy (AE proxy)
HIST ID 4 INTERVAL 10 , kinetic
# 时序步数记录（hist*_id_5.dat）/ step counter
HIST ID 5 INTERVAL 10 , step
```

---

## 5 个必需数据文件 / 5 Required Data Files

| 监测 ID / ID | 物理量 / Quantity | 文件后缀 / File Suffix | 说明 / Description |
|:---:|:---|:---|:---|
| 1 | 轴向应力 / Axial Stress | `_id_1.dat` | 顶底墙支座反力 / wall reaction force |
| 2 | 轴向应变 / Axial Strain | `_id_2.dat` | 顶底墙垂向位移差 / vertical displacement |
| 3 | 横向应变 / Lateral Strain | `_id_3.dat` | 左右监测带横向鼓胀 / lateral bulging |
| 4 | 动能 / Kinetic Energy | `_id_4.dat` | 代理声发射信号 / AE proxy signal |
| 5 | 计算步 / Time Step | `_id_5.dat` | 序列同步基准 / sequence synchronization |

程序按 `_id_X.dat` 后缀智能匹配，不限制文件名前缀长度。  
The program matches files by the `_id_X.dat` suffix regardless of the filename prefix.

---

## 算法原理 / Algorithm

- **体应变合成 / Volumetric Strain**: $\epsilon_v = \epsilon_1 - \epsilon_3$（基于二维全正标量假设 / based on 2D positive-scalar convention）
- **弹性模量 / Elastic Moduli (E, ν)**: 取 UCS 的 30% ~ 50% 区段进行线性回归 / linear regression on the 30%–50% UCS segment
- **扩容损伤点 / Crack Damage (CD)**: 体应变极大值（压缩→膨胀转折点）/ peak volumetric strain (compression-to-dilation turning point)
- **微裂缝起裂点 / Crack Initiation (CI)**: 侧向应变偏离泊松比基线达 5σ 阈值 / lateral strain deviates from Poisson baseline by 5σ
- **微裂缝闭合点 / Crack Closure (CC)**: 轴向应力反向偏离弹性基线达 5σ 阈值 / axial stress deviates backward from elastic baseline by 5σ
- **残余强度 / Residual Strength**: 失稳后末段 10% 数据均值 / mean of the final 10% post-peak data

---

## 快速开始 / Quick Start

```python
import os
from plot2D import file_io, zdem_core, zdem_plot

# 数据目录 / data directory (containing _id_X.dat files)
target_dir = r"path\to\your\zdem\data"
thickness = 1.0   # 2D 模型法向虚拟厚度 / virtual thickness (m)
stress_factor = 1e6  # Pa → MPa

# 1. 读取数据 / read monitoring data
raw_data = file_io.read_all_ids(target_dir, Thickness=thickness, stress_factor=stress_factor)

# 2. 提取力学参数与阈值 / extract mechanical parameters & thresholds
result = zdem_core.analyze_progressive_failure(raw_data)

# 3. 渲染图表 / render publication-grade figure
zdem_plot.plot_progressive_failure(raw_data, result, os.path.join(target_dir, "Progressive_Failure_Evolution.png"))
```

执行完毕后，控制台输出四阈值报告，同时生成高清全演化破裂折线图。  
After execution, the console prints a 4-threshold report and a high-resolution evolution plot is saved.

---

## 安装依赖 / Dependencies

```bash
pip install -r requirements.txt
```

**核心依赖 / Core**:
| 包 / Package | 用途 / Purpose |
|:---|:---|
| `numpy` | 数值计算 / numerical computing |
| `scipy` | 线性回归 / linear regression |
| `matplotlib` | 数据可视化 / data visualization |

---

## 项目结构 / Project Structure

```
ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds/
├── ZDEM_main_plot_damage_and_thresholds_from_dir.py  # 主入口 / main entry
├── plot2D/
│   ├── __init__.py          # 包初始化 / package init
│   ├── file_io.py           # 数据 I/O 模块 / data I/O
│   ├── zdem_core.py         # 计算引擎 / computation engine
│   └── zdem_plot.py         # 渲染引擎 / plotting engine
├── requirements.txt         # 依赖清单 / dependencies
├── LICENSE                  # MIT 许可证 / MIT license
└── README.md                # 本文件 / this file
```

---

## 开源许可 / License

本项目基于 MIT 协议开源。  
This project is open-sourced under the MIT License.

Copyright (c) 2026 包羡钧 (Bao Xianjun)
