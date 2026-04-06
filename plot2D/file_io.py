# -*- coding: utf-8 -*-
import os
import io
import numpy as np

"""
ZDEM 数据文件 I/O 模块
功能：获取目标目录下指定文件结尾的列表，并基于 Step(计算步) 进行智能时间轴对齐。
"""

import typing
import numpy.typing as npt

def get_file_list(DataDir: str, FileType: str) -> list[str]:
    """
    获取指定后缀的绝对路径文件列表
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
    读取 .dat 文件，返回二维 numpy array (第0列为step, 第1列为数值)
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
        if line.strip() != '':
            ltmp = line.split()
            array0.append([float(x) for x in ltmp])
            
    array12 = np.array(array0)
    
    # 【核心修复点】：
    # 剔除原版的 array0.reverse() 倒序逻辑。
    # 直接使用 numpy 的 argsort，强制按照第 0 列 (Step) 从小到大排序！
    # 这彻底杜绝了插值器崩溃和切片错乱的问题。
    if len(array12) > 0:
        array12 = array12[array12[:, 0].argsort()]
        
    return array12

def read_all_ids(DataDir: str, Thickness: float = 1.0, stress_factor: float = 1e6) -> dict[str, npt.NDArray[np.float64]]:
    """
    综合数据读取器：获取 ID 1 到 4 的数据，并使用插值对齐免疫不同 INTERVAL 带来的截断。
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
    
    # 提取最高频的 stress (ID 1) 计算步，作为全局“主时间轴”
    master_step = data_s1[:, 0]
    
    # 提取数组，强制取绝对值
    val_s1 = np.abs(data_s1[:, 1] / Thickness / stress_factor)
    val_e1 = np.abs(data_e1[:, 1])
    val_e3 = np.abs(data_e3[:, 1])
    val_ek = np.abs(data_ek[:, 1])
    
    # 利用 numpy 线性插值，将不同频率的数据完美映射到主时间轴上
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