# -*- coding: utf-8 -*-
import os
import io
import numpy as np
import typing
import numpy.typing as npt

"""
ZDEM 数据文件 I/O 模块
重构时间：2026-04
功能：获取目标目录下指定文件结尾的列表，并基于 Step(计算步) 进行智能时间轴对齐。
"""

def get_file_list(DataDir: str, FileType: str) -> list[str]:
    """
    输入参数：
    [1] DataDir  搜索目录
    [2] FileType 文件类型(如 '_id_1.dat')
    输出：包含绝对路径的 ListFile
    """
    pathDir = os.listdir(DataDir)
    ListFile = []
    for FileName in pathDir:
        newDir = os.path.join(DataDir, FileName)
        if os.path.isfile(newDir):
            tempFileName = os.path.split(newDir)[1]
            if tempFileName.find(FileType) != -1:
                ListFile.append(newDir)
    return ListFile

def get_file_data(filename: str) -> npt.NDArray[np.float64]:
    """
    输入参数：
    [1] filename  文件名
    输出：
    二维 numpy array 保存该文件下提取出来的数据 (第0列为step, 第1列为数值)
    """
    xfile = io.open(filename, "r", encoding='utf-8')
    flag1 = 0
    list0 = []
    
    # 逐行读取数据块，寻找 'hist' 关键字进行截断
    for line in xfile:
        if "hist" in line:
            flag1 = 1
        if flag1:
            list0.append(line)
    xfile.close()

    array0 = []
    # 从 list0 的第 3 行读到倒数第 2 行（排除首尾非数据行）
    for line in list0[3:-1]:
        if line != '\n':
            ltmp = line.split()
            for i in range(len(ltmp)):
                ltmp[i] = float(ltmp[i])
            array0.append(ltmp)
            
    # 由于 ZDEM 输入习惯，倒序转换使其成为正序时间序列 (Step 从小到大)
    array0.reverse()
    array12 = np.array(array0)
    
    return array12

def read_all_ids(DataDir: str, Thickness: float = 1.0, stress_factor: float = 1e6) -> dict[str, npt.NDArray[np.float64]]:
    """
    针对渐进破裂过程分析的综合数据读取器。
    获取对应 _id_1 到 _id_4.dat 的数据并进行截断对齐与标准化缩放。
    [核心修复] 使用 np.interp 基于计算步(step)进行插值，免疫不同 INTERVAL 造成的强制截断灾难。
    返回包含 s1, e1, e3, ek 字段的字典。
    """
    try:
        file_id1 = get_file_list(DataDir, '_id_1.dat')[-1] # 轴压
        file_id2 = get_file_list(DataDir, '_id_2.dat')[-1] # 轴变
        file_id3 = get_file_list(DataDir, '_id_3.dat')[-1] # 横变
        file_id4 = get_file_list(DataDir, '_id_4.dat')[-1] # 动能 (AE)
    except IndexError:
        raise FileNotFoundError(f"在目录 [{DataDir}] 未找到完整的 ID 1~4 数据文件，请检查！")
    
    # 获取原始二维数组 (Nx2)
    data_s1 = get_file_data(file_id1)
    data_e1 = get_file_data(file_id2)
    data_e3 = get_file_data(file_id3)
    data_ek = get_file_data(file_id4)
    
    # [魔法在这里] 提取最高频、最核心的 stress (ID 1) 的计算步，作为全局“主时间轴”
    master_step = data_s1[:, 0]
    
    # 提取数组，由于不同ZDEM压缩方向的正负有差异，强制取绝对值
    val_s1 = np.abs(data_s1[:, 1] / Thickness / stress_factor)
    val_e1 = np.abs(data_e1[:, 1])
    val_e3 = np.abs(data_e3[:, 1])
    val_ek = np.abs(data_ek[:, 1])
    
    # 利用 numpy 线性插值，将其他频率的数据完美映射到 master_step 主时间轴上
    arr_s1 = val_s1
    arr_e1 = np.interp(master_step, data_e1[:, 0], val_e1)
    arr_e3 = np.interp(master_step, data_e3[:, 0], val_e3)
    arr_ek = np.interp(master_step, data_ek[:, 0], val_ek)
    
    return {
        's1': arr_s1,
        'e1': arr_e1,
        'e3': arr_e3,
        'ek': arr_ek
    }