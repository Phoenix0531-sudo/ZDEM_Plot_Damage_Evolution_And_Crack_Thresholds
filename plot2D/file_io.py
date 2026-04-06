# -*- coding: utf-8 -*-
import os
import io
import numpy as np

"""
ZDEM 数据文件 I/O 模块
重构时间：2026-04
功能：获取目标目录下指定文件结尾的列表，并转化为 Numpy 数组。
"""

import typing
import numpy.typing as npt

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
    二维 numpy array 保存该文件下提取出来的数据
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
            
    # 由于 ZDEM 输入习惯，倒序转换使其成为正序时间序列
    array0.reverse()
    array12 = np.array(array0)
    
    return array12

def read_all_ids(DataDir: str, Thickness: float = 1.0, stress_factor: float = 1e6) -> dict[str, npt.NDArray[np.float64]]:
    """
    针对渐进破裂过程分析的综合数据读取器。
    获取对应 _id_1 到 _id_4.dat 的数据并进行截断对齐与标准化缩放。
    返回包含 s1, e1, e3, ek 字段的字典。
    """
    try:
        file_id1 = get_file_list(DataDir, '_id_1.dat')[-1] # 轴压
        file_id2 = get_file_list(DataDir, '_id_2.dat')[-1] # 轴变
        file_id3 = get_file_list(DataDir, '_id_3.dat')[-1] # 横变
        file_id4 = get_file_list(DataDir, '_id_4.dat')[-1] # 动能 (AE)
    except IndexError:
        raise FileNotFoundError(f"在目录 [{DataDir}] 未找到完整的 ID 1~4 数据文件，请检查！")
    
    # 提取数组，由于不同ZDEM压缩方向的正负有差异，强制取绝对值进行幅值统计
    arr_s1 = np.abs(get_file_data(file_id1)[:, 1] / Thickness / stress_factor)
    arr_e1 = np.abs(get_file_data(file_id2)[:, 1])
    arr_e3 = np.abs(get_file_data(file_id3)[:, 1])
    arr_ek = np.abs(get_file_data(file_id4)[:, 1])
    
    # 对齐截断数据（依靠最小行数同步数据阶段）
    min_len = min(len(arr_s1), len(arr_e1), len(arr_e3), len(arr_ek))
    
    return {
        's1': arr_s1[:min_len],
        'e1': arr_e1[:min_len],
        'e3': arr_e3[:min_len],
        'ek': arr_ek[:min_len]
    }
