# -*- coding: utf-8 -*-
"""
单轴渐进分析入口脚本
创建于：2026-04
此脚本是 ZDEM 演化破裂自动分析系统的 Demo 样例，直接将你的数据路径更换进入运行即可。
"""

import os
import sys

# 保证当前代码所在目录环境可见
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plot2D import zdem_plot

def main():
    # TODO: 请更改为包含 _id_1.dat 至 _id_5.dat 的目标数据读取文件夹
    test_data_dir = r"D:\ZDEM_Data_Simulation_Output\Test_Sample_01"
    
    # 保护措施：由于当前为了发版演示，目标可能是占位符
    if not os.path.exists(test_data_dir):
        print(f"[!] 警告：填入的测试路径 {test_data_dir} 不存在。")
        print("请手动将 target_dir 修改为包含各种 _id_.dat 的真实数据目录。")
        return

    # 调用重构后的主解析引擎：
    # Thickness 指明你的模型厚度。
    # stress_factor 用于将默认的 Pa 转变为绘图主副轴标签的 MPa。如果您的数据已经是 MPa 请传入 1，否则传入 1e6。
    print(">>> 启动自动分析与画图全流程...")
    zdem_plot.plot_full_evolution_from_SubDir(
        DataDir=test_data_dir,
        Thickness=1.0,
        stress_factor=1e6  # 1e6 把帕转化为兆帕
    )
    print(">>> 分析处理结束。请去数据目录验收生成的美图：Damage_Evolution.png")

if __name__ == "__main__":
    main()
