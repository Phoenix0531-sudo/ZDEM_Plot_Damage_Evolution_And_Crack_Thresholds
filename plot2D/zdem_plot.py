# -*- coding: utf-8 -*-
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from plot2D import file_io

"""
ZDEM 岩石渐进破裂分析与演化绘图核心模块
重构：加入弹性参数(E,v)及阈值(CC,CI,CD,UCS,Residual)自动提取，匹配顶刊极简绘图标准。
"""

def get_x_y_intervalue(x, y, interval, xli=None):
    """数据抽稀保留函数"""
    xi = [x[i] for i in range(0, len(x), interval)]
    yi = [y[i] for i in range(0, len(y), interval)]
    xl = []
    yl = []
    if xli != None:
        for i in range(0, len(xi)):
            if xli[0] <= xi[i] <= xli[1]:
                xl.append(xi[i])
                yl.append(yi[i])
    else:
        xl = xi
        yl = yi
    return xl, yl

def _find_nearest_index(array, value):
    """寻找数组中距离特定数值最接近的索引"""
    return (np.abs(np.array(array) - value)).argmin()

def plot_full_evolution_from_SubDir(DataDir, Thickness=1.0, stress_factor=1e6, out_name="Damage_Evolution.png"):
    """
    核心入口：直接喂入监控文件夹目录，提取 1-5 号 ID，输出分析报表并将特征画死。
    [1] DataDir : 目标存放 ID_*.dat 的工作目录
    [2] Thickness: 二维模拟模型厚度补偿（默认为 1.0）
    [3] stress_factor: 压力归一化因子（默认为 1e6，转 MPa）
    """
    # ====== 第一阶段：顶刊绘图样式控制 ======
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['axes.linewidth'] = 1.0  # 边框粗细

    # ====== 第二阶段：IO层提取 ======
    try:
        file_id1 = file_io.get_file_list(DataDir, '_id_1.dat')[-1] # 轴压
        file_id2 = file_io.get_file_list(DataDir, '_id_2.dat')[-1] # 轴变
        file_id3 = file_io.get_file_list(DataDir, '_id_3.dat')[-1] # 横变
        file_id4 = file_io.get_file_list(DataDir, '_id_4.dat')[-1] # 动能 (AE)
        # _id_5.dat 是 Step，在这个结构下我们的数据直接采用行长对齐
    except IndexError:
        raise FileNotFoundError(f"在目录 [{DataDir}] 未找到完整的 ID 1~4 数据文件，请检查！")
    
    # 提取数组，由于不同ZDEM压缩方向的正负有差异，我们强制取绝对值进行幅值统计，以应付多种规范。
    arr_s1 = np.abs(file_io.get_file_data(file_id1)[:, 1] / Thickness / stress_factor)
    arr_e1 = np.abs(file_io.get_file_data(file_id2)[:, 1])
    arr_e3 = np.abs(file_io.get_file_data(file_id3)[:, 1])
    arr_ek = np.abs(file_io.get_file_data(file_id4)[:, 1])
    
    # 对齐截断数据（依靠最小步数）
    min_len = min(len(arr_s1), len(arr_e1), len(arr_e3), len(arr_ek))
    s1 = arr_s1[:min_len]
    e1 = arr_e1[:min_len]
    e3 = arr_e3[:min_len]
    ek = arr_ek[:min_len]

    # 合成体力应变（基于全正标量的情况，轴缩+，侧胀-，故 ev = e1 - e3）
    ev = e1 - e3

    # ====== 第三阶段：特征计算与提取 ======
    
    # [1] UCS (峰值强度与位置)
    ucs_val = np.max(s1)
    ucs_idx = np.argmax(s1)
    
    # 在提取其他阈值时，截取峰前部分防止失效段噪声干扰
    peak_s1 = s1[:ucs_idx]
    peak_e1 = e1[:ucs_idx]
    peak_e3 = e3[:ucs_idx]
    peak_ev = ev[:ucs_idx]

    # [2] Elasticity (弹性模量与泊松比: 30%-50%区间拟合)
    s_30, s_50 = 0.3 * ucs_val, 0.5 * ucs_val
    idx_30 = _find_nearest_index(peak_s1, s_30)
    idx_50 = _find_nearest_index(peak_s1, s_50)
    
    import typing
    res_e: typing.Any = stats.linregress(peak_e1[idx_30:idx_50], peak_s1[idx_30:idx_50])
    E = float(res_e.slope if hasattr(res_e, 'slope') else res_e[0])
    b_e = float(res_e.intercept if hasattr(res_e, 'intercept') else res_e[1])
    res_poi: typing.Any = stats.linregress(peak_e1[idx_30:idx_50], peak_e3[idx_30:idx_50])
    poi_slope = float(res_poi.slope if hasattr(res_poi, 'slope') else res_poi[0])
    b_poi = float(res_poi.intercept if hasattr(res_poi, 'intercept') else res_poi[1])
    v = abs(poi_slope)
    
    # 基线预测函数定义（利用刚得出的弹性参数向两侧延拓）
    def e3_baseline(e1_target): return poi_slope * e1_target + b_poi
    def s1_baseline(e1_target): return E * e1_target + b_e

    # [3] CD (扩容点：体力应变由压缩转向膨胀的最大反射点)
    # 考虑到波形抖动，用前一段进行查找极值点
    cd_idx = np.argmax(peak_ev)
    cd_stress = s1[cd_idx]

    # [4] CI (起裂点：位于40%~UCS间，侧应变显著大于弹性的基线膨胀即微裂纹张开)
    ci_stress = 0.0
    ci_idx = 0
    tol_ci = np.std(peak_e3[idx_30:idx_50] - e3_baseline(peak_e1[idx_30:idx_50])) * 5
    if tol_ci < 1e-6: tol_ci = 1e-4

    for i in range(idx_50, ucs_idx):
        if (peak_e3[i] - e3_baseline(peak_e1[i])) > tol_ci:
            ci_idx = i
            ci_stress = s1[i]
            break

    # [5] CC (裂纹闭合：从30%反向索源，找到应变大程度偏离弹性预期的源头)
    cc_stress = 0.0
    cc_idx = 0
    tol_cc = np.std(peak_s1[idx_30:idx_50] - s1_baseline(peak_e1[idx_30:idx_50])) * 5
    if tol_cc < 1e-6: tol_cc = 1e-4

    for i in range(idx_30, 0, -1):
        if np.abs(peak_s1[i] - s1_baseline(peak_e1[i])) > tol_cc:
            cc_idx = i
            cc_stress = s1[i]
            break

    # [6] Residual (残余强度：取数据尾段10%平稳应力均值)
    residual_stress = np.mean(s1[-int(len(s1)*0.1):]) if len(s1) > 10 else s1[-1]

    # ====== 第四阶段：全局画布绘制 ======
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # 要求：四方封闭，刻度向内
    ax1.tick_params(direction='in', right=True, top=True, labelsize=12)
    
    # 绘制基础三类应变
    ax1.plot(e1, s1, 'k-', linewidth=1.2, label=r'Axial Strain ($\epsilon_1$)')
    ax1.plot(e3, s1, 'k--', linewidth=1.2, label=r'Lateral Strain ($\epsilon_3$)')
    ax1.plot(ev, s1, 'k-.', linewidth=1.2, label=r'Volumetric Strain ($\epsilon_v$)')

    # 添加水平阈值辅助线与名称标注
    ax1.axhline(y=ucs_val, color='k', linestyle=':', linewidth=0.8)
    ax1.text(np.max(e1)*0.85, ucs_val + (ucs_val*0.01), 'UCS', fontsize=12)

    ax1.axhline(y=cd_stress, color='k', linestyle=':', linewidth=0.8)
    ax1.text(np.max(e1)*0.85, cd_stress + (ucs_val*0.01), 'CD', fontsize=12)
    ax1.plot(ev[cd_idx], cd_stress, 'ko', markersize=5) # 极大值点

    if ci_stress > 0:
        ax1.axhline(y=ci_stress, color='k', linestyle=':', linewidth=0.8)
        ax1.text(np.max(e1)*0.85, ci_stress + (ucs_val*0.01), 'CI', fontsize=12)
    
    if cc_stress > 0:
        ax1.axhline(y=cc_stress, color='k', linestyle=':', linewidth=0.8)
        ax1.text(np.max(e1)*0.85, cc_stress + (ucs_val*0.01), 'CC', fontsize=12)

    ax1.set_xlabel('Strain (1)', fontsize=14)
    ax1.set_ylabel('Axial Stress (MPa)', fontsize=14)
    
    # 启用次坐标系叠加动能（Equivalent AE）以对应右侧
    ax2 = ax1.twinx()
    ax2.tick_params(direction='in', right=True, labelsize=12)
    ax2.plot(e1, ek, color='gray', linestyle=':', linewidth=1.0, label='Kinetic Energy')
    ax2.set_ylabel('Kinetic Energy (J)', fontsize=14)

    # 合并主副图例，并移除冗余框架
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=False, fontsize=11)
    
    # 储存输出图像文件
    save_path = os.path.join(DataDir, out_name)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 终端汇报数据参数
    print("="*45)
    print(f"提取任务完成 -> 目录: {DataDir}")
    print(f"弹模 E = {E:.2f} MPa, 泊松比 v = {v:.3f}")
    print(f"UCS = {ucs_val:.2f} MPa, 跌落残余 Residual = {residual_stress:.2f} MPa")
    print(f"裂纹闭合 CC = {cc_stress:.2f} MPa, 横向起裂 CI = {ci_stress:.2f} MPa, 扩容 CD = {cd_stress:.2f} MPa")
    print("="*45)

    return {
        'E': E, 'v': v, 'UCS': ucs_val, 'Residual': residual_stress,
        'CC': cc_stress, 'CI': ci_stress, 'CD': cd_stress, 'ImgPath': save_path
    }
