# -*- coding: utf-8 -*-
import numpy as np
from scipy import stats # type: ignore
import typing
import numpy.typing as npt

def _find_nearest_index(array: npt.NDArray[np.float64], value: typing.Union[float, np.floating[typing.Any]]) -> int:
    """寻找数组中距离特定数值最接近的索引"""
    return int((np.abs(np.array(array) - value)).argmin())

def analyze_progressive_failure(raw_data: dict[str, npt.NDArray[np.float64]]) -> dict[str, typing.Any]:
    """
    接收 raw_data (包含 s1, e1, e3, ek 的字典)
    返回包含所有阈值计算结果、对应的应力应变坐标点以及派生的体积应变序列 ev 的标准化字典。
    """
    s1 = raw_data['s1']
    e1 = raw_data['e1']
    e3 = raw_data['e3']
    
    # 2. 计算体积应变 ev = e1 + 2*e3（基于全正标量的情况，轴缩+，侧胀-，故 ev = e1 - e3）
    ev = e1 - e3

    # [1] UCS (峰值强度与位置)
    ucs_val = float(np.max(s1))
    ucs_idx = int(np.argmax(s1))
    
    # 在提取其他阈值时，截取峰前部分防止失效段噪声干扰
    peak_s1 = s1[:ucs_idx]
    peak_e1 = e1[:ucs_idx]
    peak_e3 = e3[:ucs_idx]
    peak_ev = ev[:ucs_idx]

    # [2] Elasticity (弹性模量与泊松比: 带有自适应容差与方差降级机制)
    # 1. 初始基准寻址：锁定 30% 到 50% UCS 之间的数据
    s_30, s_50 = 0.3 * ucs_val, 0.5 * ucs_val
    idx_30 = _find_nearest_index(peak_s1, s_30)
    idx_50 = _find_nearest_index(peak_s1, s_50)
    
    if idx_30 >= idx_50:
        idx_50 = idx_30 + 1
        if idx_50 >= len(peak_s1):
            idx_30 = max(0, len(peak_s1) - 2)
            idx_50 = len(peak_s1)
            
    # 初始化实际使用的边界，预防 Level 2 覆盖
    eff_start = idx_30
    eff_end = idx_50

    # ============== 安全机制 1: 数据方差判定 ==============
    slice_e1 = peak_e1[idx_30:idx_50]
    slice_s1 = peak_s1[idx_30:idx_50]
    slice_e3 = peak_e3[idx_30:idx_50]

    if len(np.unique(slice_e1)) < 2 or np.std(slice_e1) < 1e-8:
        print("[WARNING] 30%-50% UCS 区间内轴向应变(e1)数据方差不足（极少有效点），触发自动安全降级，扩大寻址区间...")
        
        # 3. 第二级安全降级 (扩大容差区间 10% - 60%)
        s_10, s_60 = 0.1 * ucs_val, 0.6 * ucs_val
        idx_10 = _find_nearest_index(peak_s1, s_10)
        idx_60 = _find_nearest_index(peak_s1, s_60)
        if idx_10 >= idx_60:
            idx_60 = min(len(peak_s1), idx_10 + 2)
            
        slice_e1 = peak_e1[idx_10:idx_60]
        slice_s1 = peak_s1[idx_10:idx_60]
        slice_e3 = peak_e3[idx_10:idx_60]
        eff_start = idx_10
        eff_end = idx_60

        # 兜底校验
        if len(np.unique(slice_e1)) < 2 or np.std(slice_e1) < 1e-8:
            print("[WARNING] Level 2 切片数据仍极度匮乏或为常数，启动最终兜底割线模量算法...")
            # 步骤 3: 容错算法重构 (Fallback) 强制取终点和起点相减求割线斜率
            e1_start_val = float(slice_e1[0])
            e1_end_val = float(slice_e1[-1])
            s1_start_val = float(slice_s1[0])
            s1_end_val = float(slice_s1[-1])
            
            # 防御被除数为0或无穷大引发的致命数学异常
            delta_e1 = e1_end_val - e1_start_val
            if delta_e1 == 0 or not np.isfinite(delta_e1):
                delta_e1 = 1e-12
                
            fallback_E = (s1_end_val - s1_start_val) / delta_e1
            
            return {
                'UCS': ucs_val,
                'E': fallback_E,
                'v': 0.25, # 兜底泊松比
                'CD': 0.0,
                'CI': 0.0,
                'CC': 0.0,
                'cd_idx': 0,
                'ci_idx': 0,
                'ev': np.zeros_like(s1),
                'eps_v_spline': np.zeros_like(s1)
            }

    # 5. 线性回归计算参数计算标准
    # 杨氏模量 E = σ1 对 ϵ1 回归的斜率
    res_e: typing.Any = stats.linregress(slice_e1, slice_s1)
    E = float(res_e.slope if hasattr(res_e, 'slope') else res_e[0])
    b_e = float(res_e.intercept if hasattr(res_e, 'intercept') else res_e[1])

    # 泊松比 v = −ϵ3（横向应变取反）对 ϵ1 回归的斜率
    neg_slice_e3 = -np.array(slice_e3)
    res_v: typing.Any = stats.linregress(slice_e1, neg_slice_e3)
    v = float(res_v.slope if hasattr(res_v, 'slope') else res_v[0])

    # 为了建立后续基线，提取原生的 e3 对 e1 回归特性
    res_poi: typing.Any = stats.linregress(slice_e1, slice_e3)
    poi_slope = float(res_poi.slope if hasattr(res_poi, 'slope') else res_poi[0])
    b_poi = float(res_poi.intercept if hasattr(res_poi, 'intercept') else res_poi[1])
    
    # 用作兼容后续阈值寻址使用的区间边界别名（对应当前生效的有效线性区间）
    idx_30 = eff_start
    idx_50 = eff_end

    # 基线预测函数定义（利用刚得出的弹性参数向两侧延拓）
    def e3_baseline(e1_target: typing.Any) -> typing.Any: return poi_slope * e1_target + b_poi
    def s1_baseline(e1_target: typing.Any) -> typing.Any: return E * e1_target + b_e

    # [3] CD (扩容点：体力应变由压缩转向膨胀的最大反射点)
    # 考虑到波形抖动，用前一段进行查找极值点
    cd_idx = int(np.argmax(peak_ev))
    cd_stress = float(s1[cd_idx])

    # [4] CI (起裂点：位于40%~UCS间，侧应变显著大于弹性的基线膨胀即微裂纹张开)
    ci_stress = 0.0
    ci_idx = 0
    tol_ci = float(np.std(peak_e3[idx_30:idx_50] - e3_baseline(peak_e1[idx_30:idx_50])) * 5)
    if tol_ci < 1e-6: tol_ci = 1e-4

    for i in range(idx_50, ucs_idx):
        if (peak_e3[i] - e3_baseline(peak_e1[i])) > tol_ci:
            ci_idx = i
            ci_stress = float(s1[i])
            break

    # [5] CC (裂纹闭合：从30%反向索源，找到应变大程度偏离弹性预期的源头)
    cc_stress = 0.0
    cc_idx = 0
    tol_cc = float(np.std(peak_s1[idx_30:idx_50] - s1_baseline(peak_e1[idx_30:idx_50])) * 5)
    if tol_cc < 1e-6: tol_cc = 1e-4

    for i in range(idx_30, 0, -1):
        if np.abs(peak_s1[i] - s1_baseline(peak_e1[i])) > tol_cc:
            cc_idx = i
            cc_stress = float(s1[i])
            break

    # [6] Residual (残余强度：取数据尾段10%平稳应力均值)
    residual_stress = np.mean(s1[-int(len(s1)*0.1):]) if len(s1) > 10 else s1[-1]

    # 终端汇报数据参数
    print("="*45)
    print(f"渐进破裂计算引擎已执行")
    print(f"弹模 E = {E:.2f} MPa, 泊松比 v = {v:.3f}")
    print(f"UCS = {ucs_val:.2f} MPa, 跌落残余 Residual = {residual_stress:.2f} MPa")
    print(f"裂纹闭合 CC = {cc_stress:.2f} MPa, 横向起裂 CI = {ci_stress:.2f} MPa, 扩容 CD = {cd_stress:.2f} MPa")
    print("="*45)

    return {
        'ev': ev,
        'E': E, 'v': v, 'UCS': ucs_val, 'Residual': residual_stress,
        'CC': cc_stress, 'CI': ci_stress, 'CD': cd_stress,
        'cd_idx': cd_idx
    }
