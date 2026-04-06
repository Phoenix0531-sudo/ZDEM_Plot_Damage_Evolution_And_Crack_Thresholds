# ZDEM_Plot_Damage_Evolution_And_Crack_Thresholds

- **维护人**：包羡钧

## 0. 数据准备 (ZDEM 脚本设置)

在运行本分析系统之前，您需要确保在 ZDEM 模拟脚本中包含以下监测指令，以导出必要的 `.dat` 文件：

```bash
# 通过顶底部墙体移动距离，计算轴向应力，保存到 hist*_id_2.dat
HIST ID 1 INTERVAL 1 , gstress group top_wall
HIST ID 2 INTERVAL 1 , gstrain group top_wall|bom_wall 
# 框选试件最左侧边缘
PROP group p_left range x 2000.0 2100.0 y 3000.0 11000.0
# 框选试件最右侧边缘
PROP group p_right range x 5900.0 6000.0 y 3000.0 11000.0
# 监测左右颗粒组之间的相对距离变化 (横向应变)
HIST ID 3 INTERVAL 1 , gstrain group p_left|p_right
# 记录颗粒体系动能
HIST ID 4 INTERVAL 10 , kinetic
HIST ID 5 INTERVAL 10 , step
```

## 1. 物理监测要求 (数据输入端)

在运行本程序进行渐进破裂分析前，必须确保您的 ZDEM 脚本在加载或受压模拟段中，精确导出了以下 5 个特征数据文件，他们是提取各种阀值的基础：

1. **ID 1**: 轴向载荷/应力 (`_id_1.dat`) —— 通常通过监测顶底墙的支座拉压（例如 `gstress` ）获得。
2. **ID 2**: 轴向应变 (`_id_2.dat`) —— 基于顶底墙或特定上下特征颗粒的垂向位移差换算 (`gstrain`) 得到。
3. **ID 3**: 横向应变 (`_id_3.dat`) —— 基于左右监控带或特征组颗粒的水平向外鼓胀位移差换算得到。
4. **ID 4**: 动能体系总量 (`_id_4.dat`) —— 直接输出体系总体动能，可代理为岩石模拟中的宏观声发射（Acoustic Emission）信号。
5. **ID 5**: 时序步数 (`_id_5.dat`) —— 输出计算累计步骤，用以同步所有序列。

请注意：程序将按如上 `_id_X.dat` 的后缀智能匹配数据，并不挑剔前面的命名头长度。

## 2. 工具算法与计算逻辑

核心子函数为 `plot2D.zdem_plot.plot_full_evolution_from_SubDir`，其在处理过程中已采取绝对值转换。
具体物理过程算法如下：

- **体应变合成**：对于二维模型，由于压缩变形和膨胀变形符号转换成全正尺度处理，我们采取 $\epsilon_v = \epsilon_1 - \epsilon_3$ 去代理计算。
- **弹性模量 (E, ν)**：以抗压峰值（UCS）的 30% ~ 50% 区段作为稳定的线弹性区段进行多项式一阶提取。
- **扩容损伤点 (CD: Crack Damage)**：提取向压缩发展体应变之 **极大值（导数反向偏移点）**。
- **微裂缝起裂点 (CI: Crack Initiation)**：从 50% UCS 后朝向主峰逼近，提取由微观滑移引起的测向应变 $\epsilon_3$ 异常，当它脱离“泊松比拟合线弹性基线”达到统计学阈值时，自动确认为起裂源头点。
- **微裂缝闭合点 (CC: Crack Closure)**：同理，自 30% UCS 往前向非弹性前段索源定位 $\epsilon_1$ 的基准线大幅度背离点。
- **衰减与跌落残余 (Residual)**：默认由失稳跌落后系统稳定最后期的均值作为该受加载样本的最终支撑抵抗带。

## 3. 运行指南

您可以直接运行 `ZDEM_main_plot_damage_and_thresholds_from_dir.py` 进行单次结果的抽水：

```python
import os
from plot2D import zdem_plot

# 确定你的数据存放目标（里面涵盖上文强调的 _id_X.dat）
# 注: 此处是模拟导出数据所在文件夹
target_dir = r"X:\your\zdem\data_files\here"

# 调用主分析架构！一键到底
result = zdem_plot.plot_full_evolution_from_SubDir(target_dir, Thickness=1.0)
```

执行完毕后，不仅控制台会高光打印四大阈值报告，还会在被查询目录内落地出一张极其清爽、全黑白线型无色的【顶刊专供・全演化破裂带折线图】。
