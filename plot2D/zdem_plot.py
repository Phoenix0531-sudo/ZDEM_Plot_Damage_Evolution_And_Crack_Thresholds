import typing
import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt

"""
ZDEM 岩石图表渲染引擎 (纯绘制模块)
重构：完全解耦数学计算，仅负责按照学术顶级期刊标准渲染数据和阈值标记。
"""

def get_x_y_intervalue(x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], interval: int, xli: typing.Optional[tuple[float, float]] = None) -> tuple[list[float], list[float]]:
    """数据抽稀保留函数"""
    xi: list[float] = [float(x[i]) for i in range(0, len(x), interval)]
    yi: list[float] = [float(y[i]) for i in range(0, len(y), interval)]
    
    xl: list[float] = []
    yl: list[float] = []
    if xli:
        for i in range(len(xi)):
            if xli[0] <= xi[i] <= xli[1]:
                xl.append(xi[i])
                yl.append(yi[i])
    else:
        xl = xi
        yl = yi
    return xl, yl

def plot_progressive_failure(raw_data: dict[str, npt.NDArray[np.float64]], mechanics_results: dict[str, typing.Any], output_path: str) -> None:
    """
    纯渲染引擎：接收对齐后的原始数据及分析引擎提取的特征点，
    生成包含宏观弹性参数与破裂阈值的学术标准演化图床。
    """
    # ====== 第一阶段：顶刊绘图样式控制 ======
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['axes.linewidth'] = 1.0  # 边框粗细
    
    # 抽取坐标数据
    s1 = raw_data['s1']
    e1 = raw_data['e1']
    e3 = raw_data['e3']
    ek = raw_data['ek']
    ev = mechanics_results['ev']

    # 抽取关键力学标注信息
    ucs_val = mechanics_results['UCS']
    cd_stress = mechanics_results['CD']
    cd_idx = mechanics_results['cd_idx']
    ci_stress = mechanics_results['CI']
    cc_stress = mechanics_results['CC']

    # ====== 第二阶段：全局画布绘制 ======
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # 要求：四方封闭，刻度向内
    ax1.tick_params(direction='in', right=True, top=True, labelsize=12)
    
    # 绘制基础三类应变
    _ = ax1.plot(e1, s1, color="red", linestyle="solid", linewidth=3)
    _ = ax1.plot(-e3, s1, color="green", linestyle="solid", linewidth=3)
    _ = ax1.plot(ev, s1, color="orange", linestyle="solid", linewidth=3)

    # 添加水平阈值辅助线与名称标注
    _ = ax1.axhline(y=ucs_val, color='k', linestyle=':', linewidth=0.8)
    _ = ax1.text(x=float(np.max(e1) * 0.85), y=float(ucs_val + (ucs_val * 0.01)), s='UCS', fontsize=12)

    if cd_stress > 0:
        _ = ax1.axhline(y=cd_stress, xmin=0, xmax=0.9, color="blue", linestyle="dashed", linewidth=1.5, alpha=0.8)
        _ = ax1.text(x=float(np.amax(e1) * 0.95), y=float(cd_stress), s=f"CD: {cd_stress:.1f} MPa", color="blue",
                fontsize=11, fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    if ci_stress > 0:
        _ = ax1.axhline(y=ci_stress, xmin=0, xmax=0.9, color="purple", linestyle="dashed", linewidth=1.5, alpha=0.8)
        _ = ax1.text(x=float(np.amax(e1) * 0.95), y=float(ci_stress), s=f"CI: {ci_stress:.1f} MPa", color="purple",
                fontsize=11, fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    if cc_stress > 0:
        _ = ax1.axhline(y=cc_stress, color='k', linestyle=':', linewidth=0.8)
        _ = ax1.text(x=float(np.max(e1) * 0.85), y=float(cc_stress + (ucs_val * 0.01)), s='CC', fontsize=12)

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
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"渲染完毕 -> 图片已存储至: {output_path}")
