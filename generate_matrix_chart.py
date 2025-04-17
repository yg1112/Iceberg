import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from datetime import datetime

# 设置中文字体支持
mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']  # 优先使用这些中文字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建图表
fig, ax = plt.subplots(figsize=(10, 8))

# 数据点
x = [28.3, 22.5, 30.8, 25.6, 32.0, 40.2, 35.8, 45.5, 38.3, 42.1]  # 供应分数
y = [82.5, 78.6, 75.3, 72.4, 71.2, 55.6, 48.9, 46.2, 42.7, 41.8]  # 需求分数

# 颜色：黄金区域为红色，其他区域用不同颜色
colors = ['#FF5733', '#FF5733', '#FF5733', '#FF5733', '#FF5733', 
          '#FFC300', '#FFC300', '#DAF7A6', '#DAF7A6', '#DAF7A6']

# 绘制散点图
ax.scatter(x, y, c=colors, s=100, alpha=0.7, edgecolors='black')

# 设置标题和轴标签
ax.set_title('市场需求雷达 - 需求与供应矩阵分析 (2025-04-16)', fontsize=16)
ax.set_xlabel('供应分数 (越低表示市场供应越少)', fontsize=12)
ax.set_ylabel('需求分数 (越高表示市场需求越大)', fontsize=12)

# 设置网格和坐标范围
ax.grid(True, linestyle='--', alpha=0.7)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)

# 添加分界线
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=30, color='gray', linestyle='--', alpha=0.5)

# 标记四个象限
ax.text(15, 75, '黄金区域\n(高需求低竞争)', ha='center', fontsize=10, 
        bbox=dict(facecolor='gold', alpha=0.1))
ax.text(65, 75, '竞争区域\n(高需求高竞争)', ha='center', fontsize=10, 
        bbox=dict(facecolor='lightblue', alpha=0.1))
ax.text(15, 25, '机会缺失区域\n(低需求低竞争)', ha='center', fontsize=10, 
        bbox=dict(facecolor='lightgray', alpha=0.1))
ax.text(65, 25, '饱和区域\n(低需求高竞争)', ha='center', fontsize=10, 
        bbox=dict(facecolor='lightgray', alpha=0.1))

# 添加数据点标签
labels = ['跨平台隐私保护工具', '智能电池优化助手', '生产力习惯培养系统', '多源信息整理助手', 
          '创意写作辅助工具', '微习惯培养应用', '自定义通知管理器', '极简主义数字助手', 
          '视频内容管理平台', '自动化工作流生成器']

for i, label in enumerate(labels):
    ax.annotate(label, (x[i], y[i]), xytext=(0, 10), 
                textcoords='offset points', ha='center', fontsize=8)

# 生成时间标记
date_str = datetime.now().strftime('%Y-%m-%d')
ax.text(50, -10, f'生成时间: {date_str}', ha='center', fontsize=10, 
        transform=ax.transData)

# 调整布局并保存
plt.tight_layout()
filename = f'reports/demand_supply_matrix_{date_str}.png'
plt.savefig(filename, dpi=300, bbox_inches='tight')
print(f'图表已保存到 {filename}') 