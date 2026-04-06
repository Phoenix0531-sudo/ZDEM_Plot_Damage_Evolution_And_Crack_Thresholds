# -*- coding: utf-8 -*-
# =============================================================================
# ZDEM 岩石单轴渐进破裂与损伤阈值分析系统
# 
# 维护人：包羡钧
#
# 核心功能：
# 1. 批量读取 ZDEM 单轴压缩微观监测数据 (_id_1.dat 至 _id_5.dat)
# 2. 自动化合成体积应变
# 3. 提取宏观弹性参数 (E, v) 与渐进破裂阈值 (CC, CI, CD, UCS)
# 4. 渲染并输出高规学术全应变-能量演化图表
# =============================================================================

import os
import sys

# 挂载底层模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plot2D import file_io, zdem_core, zdem_plot

# =============================================================================
# [1] 全局参数配置区 (Global Configurations)
# =============================================================================

# 数据输入目录 (绝对或相对路径，需确保内部包含完整的 ID 监控文件)
DataDir = r"E:\0.Information\4.Temp\StructLab\Rock Mechanics\N1j_Mudrock\uniaxial\data"

# 物理模型对齐参数
Thickness = 1.0          # 2D 模型的法向虚拟厚度 (m)，默认 1.0
stress_factor = 1e6      # 应力降维因子 (1e6 代表将底层 Pa 转换为标称 MPa)

# 图像输出配置
OutputFigName = "Progressive_Failure_Evolution.png"

# =============================================================================
# [2] 核心执行逻辑 (Execution Logic)
# =============================================================================

def main():
    print(f"[INFO] 初始化分析系统...")
    print(f"[INFO] 目标数据路径: {DataDir}")
    
    if not os.path.exists(DataDir):
        print(f"[ERROR] 路径解析失败，指定的目录不存在。")
        sys.exit(1)

    try:
        # 1. 读数据 (I/O)
        print("[INFO] 开始读取并对齐微观监控原始数据...")
        raw_data = file_io.read_all_ids(DataDir, Thickness=Thickness, stress_factor=stress_factor)
        
        # 2. 算参数 (纯数学运算)
        print("[INFO] 进入计算引擎提取宏观力学特征与渐进损伤阈值...")
        mechanics_results = zdem_core.analyze_progressive_failure(raw_data)
        
        # 3. 画图 (纯渲染)
        print("[INFO] 调用纯渲染引擎生成学术出版物级别的图表...")
        output_path = os.path.join(DataDir, OutputFigName)
        zdem_plot.plot_progressive_failure(raw_data, mechanics_results, output_path)

        print(f"[INFO] 力学参数提取与图表渲染完毕。")
        
    except Exception as e:
        import traceback
        print(f"[ERROR] 引擎处理中断，捕获到异常: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()