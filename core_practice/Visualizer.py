# Visualizer.py
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import os
plt.rcParams['font.family'] = ['SimHei']    #允许中文字体显示
plt.rcParams['axes.unicode_minus'] = False  #解决符号显示问题
plt.rcParams['figure.dpi'] = 240            #超高清图片

class PackingVisualizer:
    def __init__(self):
        self.colors = {
            '标准件': '#4285F4',  # Google蓝
            '易碎件': '#EA4335',  # Google红
            '定向件': '#34A853'  # Google绿
        }

    def plot_3d_packing(self, truck, packing_plan, title="装箱方案", save_path=None):
        """
        生成3D装箱可视化图
        """
        fig = plt.figure(figsize=(15, 10))

        # 1. 3D主图
        ax1 = fig.add_subplot(221, projection='3d')
        self._plot_3d_view(ax1, truck, packing_plan, view_angle=(20, 55))
        ax1.set_title(f'{title} - 3D视图')

        # 2. XY平面投影
        ax2 = fig.add_subplot(222)
        self._plot_xy_projection(ax2, truck, packing_plan)
        ax2.set_title('XY平面投影')
        ax2.set_aspect('equal')

        # 3. XZ平面投影
        ax3 = fig.add_subplot(223)
        self._plot_xz_projection(ax3, truck, packing_plan)
        ax3.set_title('XZ平面投影')
        ax3.set_aspect('equal')

        # 4. YZ平面投影
        ax4 = fig.add_subplot(224)
        self._plot_yz_projection(ax4, truck, packing_plan)
        ax4.set_title('YZ平面投影')
        ax4.set_aspect('equal')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, format='pdf', bbox_inches='tight')
            print(f"可视化图已保存: {save_path}")

        plt.show()

    def _plot_3d_view(self, ax, truck, packing_plan, view_angle=(30, 45)):
        """绘制3D视图"""
        # 设置坐标轴
        ax.set_xlim([0, truck.L])
        ax.set_ylim([0, truck.W])
        ax.set_zlim([0, truck.H])
        ax.set_xlabel('X (cm)')
        ax.set_ylabel('Y (cm)')
        ax.set_zlabel('Z (cm)')
        ax.view_init(*view_angle)

        # 绘制车厢轮廓
        self._draw_truck_outline(ax, truck)

        # 绘制货物
        for item in packing_plan:
            self._draw_cargo(ax, item)

    def _plot_xy_projection(self, ax, truck, packing_plan):
        """XY平面投影"""
        ax.set_xlim([0, truck.L])
        ax.set_ylim([0, truck.W])
        ax.set_xlabel('X (cm)')
        ax.set_ylabel('Y (cm)')
        ax.plot([0, truck.L, truck.L, 0, 0],
                [0, 0, truck.W, truck.W, 0],
                'k-', linewidth=2)

        # 绘制货物投影
        for item in packing_plan:
            x, y, z = item['position']
            l, w, h = item['dimensions']
            color = self.colors.get(item['type'], 'gray')

            rect = plt.Rectangle((x, y), l, w,
                                 facecolor=color, alpha=0.6, edgecolor='black')
            ax.add_patch(rect)


    def _plot_xz_projection(self, ax, truck, packing_plan):
        """XZ平面投影"""
        ax.set_xlim([0, truck.L])
        ax.set_ylim([0, truck.H])
        ax.set_xlabel('X (cm)')
        ax.set_ylabel('Z (cm)')
        ax.plot([0, truck.L, truck.L, 0, 0],
                [0, 0, truck.H, truck.H, 0],
                'k-', linewidth=2)

        for item in packing_plan:
            x, y, z = item['position']
            l, w, h = item['dimensions']
            color = self.colors.get(item['type'], 'gray')

            rect = plt.Rectangle((x, z), l, h,
                                 facecolor=color, alpha=0.6, edgecolor='black')
            ax.add_patch(rect)

    def _plot_yz_projection(self, ax, truck, packing_plan):
        """YZ平面投影"""
        ax.set_xlim([0, truck.W])
        ax.set_ylim([0, truck.H])
        ax.set_xlabel('Y (cm)')
        ax.set_ylabel('Z (cm)')
        ax.plot([0, truck.W, truck.W, 0, 0],
                [0, 0, truck.H, truck.H, 0],
                'k-', linewidth=2)

        for item in packing_plan:
            x, y, z = item['position']
            l, w, h = item['dimensions']
            color = self.colors.get(item['type'], 'gray')

            rect = plt.Rectangle((y, z), w, h,
                                 facecolor=color, alpha=0.6, edgecolor='black')
            ax.add_patch(rect)

    def _draw_truck_outline(self, ax, truck):
        """绘制车厢轮廓"""
        # 绘制底部
        X, Y = np.meshgrid([0, truck.L], [0, truck.W])
        Z = np.zeros_like(X)
        ax.plot_surface(X, Y, Z, alpha=0.1, color='gray')

        # 绘制顶部
        Z_top = np.ones_like(X) * truck.H
        ax.plot_surface(X, Y, Z_top, alpha=0.1, color='gray')

    def _draw_cargo(self, ax, item):
        """绘制单个货物"""
        x, y, z = item['position']
        l, w, h = item['dimensions']
        color = self.colors.get(item['type'], 'gray')

        # 绘制立方体
        ax.bar3d(x, y, z, l, w, h,
                 color=color, alpha=0.5, edgecolor='black', linewidth=1)

    def plot_algorithm_bar_chart(self, algorithm_data, save_path=None):
        """
        绘制算法性能柱状图（简洁版）
        algorithm_data: 上面的字典格式
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        algorithms = list(algorithm_data.keys())
        x = np.arange(len(algorithms))
        width = 0.6

        # 1. 体积利用率对比
        volume_ratios = [algorithm_data[a]['体积利用率'] for a in algorithms]
        ax1 = axes[0, 0]
        bars1 = ax1.bar(x, volume_ratios, width, color='#6baedd', edgecolor='white', linewidth=1.5)
        ax1.set_ylabel('体积利用率')
        ax1.set_title('体积利用率对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(algorithms, rotation=0)
        ax1.set_ylim(0, max(volume_ratios) * 1.1)
        ax1.grid(True, alpha=0.3, axis='y')

        # 在柱子上添加数值
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, height + 0.01,  # 向上偏移一点
                     f'{height:.2%}', ha='center', va='bottom',
                     fontsize=10, weight='bold')  # 加粗、变大

        # 2. 重量利用率对比
        weight_ratios = [algorithm_data[a]['重量利用率'] for a in algorithms]
        ax2 = axes[0, 1]
        bars2 = ax2.bar(x, weight_ratios, width, color='#f28b82', edgecolor='white', linewidth=1.5)
        ax2.set_ylabel('重量利用率')
        ax2.set_title('重量利用率对比')
        ax2.set_xticks(x)
        ax2.set_xticklabels(algorithms, rotation=0)
        ax2.set_ylim(0, max(weight_ratios) * 1.1)
        ax2.grid(True, alpha=0.3, axis='y')

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, height + 0.01,  # 向上偏移一点
                     f'{height:.2%}', ha='center', va='bottom',
                     fontsize=10, weight='bold')  # 加粗、变大

        # 3. 综合适应度对比
        fitness_scores = [algorithm_data[a]['综合适应度'] for a in algorithms]
        ax3 = axes[1, 0]
        bars3 = ax3.bar(x, fitness_scores, width, color='#81c995', edgecolor='white', linewidth=1.5)
        ax3.set_ylabel('综合适应度')
        ax3.set_title('综合适应度对比')
        ax3.set_xticks(x)
        ax3.set_xticklabels(algorithms, rotation=0)
        ax3.set_ylim(0, max(fitness_scores) * 1.1)
        ax3.grid(True, alpha=0.3, axis='y')

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2, height + 0.01,  # 向上偏移一点
                     f'{height:.2%}', ha='center', va='bottom',
                     fontsize=10, weight='bold')  # 加粗、变大

        # 4. 计算时间对比
        compute_times = [algorithm_data[a]['计算时间'] for a in algorithms]
        ax4 = axes[1, 1]
        bars4 = ax4.bar(x, compute_times, width, color='#fbbc04', edgecolor='white', linewidth=1.5)
        ax4.set_ylabel('计算时间 (秒)')
        ax4.set_title('计算时间对比')
        ax4.set_xticks(x)
        ax4.set_xticklabels(algorithms, rotation=0)
        ax4.set_ylim(0, max(compute_times) * 1.1)
        ax4.grid(True, alpha=0.3, axis='y')

        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width() / 2, height + 0.1,  # 【修改点】偏移量改大一点
                     f'{height:.2f}s', ha='center', va='bottom',  # 【修改点】去掉%，改成普通格式
                     fontsize=10, weight='bold')

        plt.suptitle('算法性能对比分析', fontsize=16)
        plt.tight_layout()


        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', format='pdf')
            print(f"算法对比图已保存: {save_path}")

        plt.show()

    def plot_cargo_comparison(self, layered_data, tradeoff_data, save_path=None):
        """
        绘制两种算法的货物分布对比图（简化版）
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        cargo_types = ['G4', 'G5', 'G3', 'G1', 'G2']
        x = np.arange(len(cargo_types))
        width = 0.35

        # 1. 装载数量对比
        layered_counts = [layered_data[t]['count'] for t in cargo_types]
        tradeoff_counts = [tradeoff_data[t]['count'] for t in cargo_types]

        ax1 = axes[0]
        ax1.bar(x - width / 2, layered_counts, width, label='分层装载', color='blue', alpha=0.7)
        ax1.bar(x + width / 2, tradeoff_counts, width, label='体积重量权衡', color='green', alpha=0.7)

        ax1.set_xlabel('货物类型')
        ax1.set_ylabel('装载数量 (件)')
        ax1.set_title('装载数量对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(cargo_types)
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')

        # 2. 装载率对比
        layered_rates = [layered_data[t]['装载率'] for t in cargo_types]
        tradeoff_rates = [tradeoff_data[t]['装载率'] for t in cargo_types]

        ax2 = axes[1]
        ax2.plot(x, layered_rates, 'o-', label='分层装载', color='#4a6cf3', linewidth=2)
        ax2.plot(x, tradeoff_rates, 's--', label='体积重量权衡', color='#4caf50', linewidth=2)

        ax2.set_xlabel('货物类型')
        ax2.set_ylabel('装载率')
        ax2.set_title('装载率对比')
        ax2.set_xticks(x)
        ax2.set_xticklabels(cargo_types)
        ax2.set_ylim([0, 1.1])
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 突出G3的差异
        ax2.annotate(
            '能装易碎件',
            xy=(2, tradeoff_rates[2]),
            xytext=(2, 0.4),  # 文字位置上移，避开折线
            arrowprops=dict(arrowstyle='->', color='red', shrinkA=5, shrinkB=5),
            ha='center', color='red', fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.9)  # 加白色背景框
        )

        # 3. 重量分布
        layered_weights = [layered_data[t]['total_weight'] for t in cargo_types]
        tradeoff_weights = [tradeoff_data[t]['total_weight'] for t in cargo_types]

        ax3 = axes[2]
        ax3.bar(x - width / 2, layered_weights, width, label='分层装载', color='blue', alpha=0.7)
        ax3.bar(x + width / 2, tradeoff_weights, width, label='体积重量权衡', color='green', alpha=0.7)

        ax3.set_xlabel('货物类型')
        ax3.set_ylabel('总重量 (kg)')
        ax3.set_title('重量分布对比')
        ax3.set_xticks(x)
        ax3.set_xticklabels(cargo_types)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        plt.suptitle('货物类型分布对比：分层装载 vs 体积重量权衡', fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', format='pdf')
            print(f"货物对比图已保存: {save_path}")

        plt.show()