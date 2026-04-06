# -*- coding: utf-8 -*-
import os
import io
import numpy as np

"""
ZDEM 数据文件 I/O 模块
重构时间：2026-04
功能：获取目标目录下指定文件结尾的列表，并转化为 Numpy 数组。
"""

def get_file_list(DataDir, FileType):
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

def get_file_data(filename):
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
