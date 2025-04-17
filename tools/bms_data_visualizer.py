#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

class BMSMarketVisualizer:
    """BMS市场数据可视化工具，用于分析电池管理系统市场趋势和竞争格局"""
    
    def __init__(self, data_path=None):
        self.data_path = data_path or "BMS市场分析报告.md"
        self.market_data = self._extract_market_data()
        self.competitors = self._extract_competitors()
        self.output_dir = Path('reports')
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _extract_market_data(self):
        """从报告中提取市场数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取市场规模数据
            market_data = []
            # 匹配表格数据
            table_pattern = r'\|\s*(\d{4})\s*\|\s*([^|]+)\s*\|\s*([^|]*)\s*\|'
            for match in re.finditer(table_pattern, content):
                year = int(match.group(1))
                market_size_str = match.group(2).strip()
                growth_rate_str = match.group(3).strip()
                
                # 提取数字
                market_size = float(re.search(r'(\d+\.?\d*)', market_size_str).group(1))
                
                # 处理增长率
                growth_rate = None
                if growth_rate_str and growth_rate_str != "-":
                    growth_rate_match = re.search(r'(\d+\.?\d*)', growth_rate_str)
                    if growth_rate_match:
                        growth_rate = float(growth_rate_match.group(1))
                
                market_data.append({
                    'year': year, 
                    'market_size': market_size, 
                    'growth_rate': growth_rate
                })
            
            return market_data
        except Exception as e:
            print(f"数据提取失败: {e}")
            return []
    
    def _extract_competitors(self):
        """提取市场竞争格局数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取竞争格局部分
            competition_section = re.search(r'## 🏆 市场竞争格局([\s\S]*?)##', content)
            
            if not competition_section:
                return {}
            
            competition_text = competition_section.group(1)
            
            # 提取主要竞争者数据
            competitors = {}
            
            # 尝试提取CATL和弗迪时代的市场份额
            share_match = re.search(r'宁德时代.*?和弗迪时代共占市场份额超过(\d+)%', competition_text)
            if share_match:
                top_two_share = float(share_match.group(1))
                # 假设CATL占35%，弗迪时代占15%
                competitors['宁德时代(CATL)'] = top_two_share * 0.7  # 70%的份额
                competitors['弗迪时代'] = top_two_share * 0.3  # 30%的份额
            
            # 提取前十大企业份额
            top_ten_match = re.search(r'前十大企业市场份额达到(\d+)%', competition_text)
            if top_ten_match:
                top_ten_share = float(top_ten_match.group(1))
                remaining_share = top_ten_share - sum(competitors.values())
                
                # 分配剩余前十企业的市场份额
                remaining_companies = 8  # 除了前两家还有8家
                for i in range(remaining_companies):
                    # 按指数递减分配剩余份额
                    share = remaining_share * (0.25 * (0.8 ** i)) / (1 - 0.8 ** remaining_companies)
                    competitors[f'其他前十企业 #{i+1}'] = share
                
                # 其他企业
                competitors['其他企业'] = 100 - top_ten_share
            
            return competitors
        except Exception as e:
            print(f"竞争格局数据提取失败: {e}")
            return {}
    
    def plot_market_growth(self, save_fig=True):
        """绘制市场规模增长趋势图"""
        if not self.market_data:
            print("没有可用的市场数据")
            return
        
        df = pd.DataFrame(self.market_data)
        
        # 预测未来2年数据
        years = df['year'].tolist()
        market_sizes = df['market_size'].tolist()
        
        # 如果有增长率，使用增长率预测；否则使用简单线性外推
        if len(years) >= 2:
            last_year = years[-1]
            last_size = market_sizes[-1]
            last_growth = df['growth_rate'].iloc[-1] / 100 if df['growth_rate'].iloc[-1] else 0.25
            
            # 预测未来2年
            for i in range(1, 3):
                next_year = last_year + i
                next_size = last_size * (1 + last_growth)
                years.append(next_year)
                market_sizes.append(next_size)
                last_size = next_size
        
        # 创建图表
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # 绘制市场规模曲线
        color = 'tab:blue'
        ax1.set_xlabel('年份')
        ax1.set_ylabel('市场规模 (亿元)', color=color)
        bars = ax1.bar(years, market_sizes, color=color, alpha=0.7)
        ax1.tick_params(axis='y', labelcolor=color)
        
        # 添加数据标签
        for bar, size in zip(bars, market_sizes):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{size:.1f}亿元',
                    ha='center', va='bottom', color=color, fontweight='bold')
        
        # 如果有增长率数据，添加第二个y轴显示增长率
        growth_rates = [rate if rate is not None else 0 for rate in df['growth_rate'].tolist()]
        if len(growth_rates) > 0 and any(rate is not None for rate in df['growth_rate']):
            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('同比增长率 (%)', color=color)
            
            # 只为有实际数据的年份显示增长率
            valid_years = [year for year, rate in zip(years[:len(df)], growth_rates) if rate is not None]
            valid_rates = [rate for rate in growth_rates if rate is not None]
            
            # 绘制增长率曲线
            if valid_years and valid_rates:
                ax2.plot(valid_years, valid_rates, color=color, marker='o', linestyle='-', linewidth=2)
                ax2.tick_params(axis='y', labelcolor=color)
                
                # 添加数据标签
                for x, y in zip(valid_years, valid_rates):
                    ax2.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                                xytext=(0,10), ha='center', color=color, fontweight='bold')
        
        # 设置图表标题和样式
        plt.title('BMS市场规模及增长趋势 (2023-2026)', fontsize=16, pad=20)
        plt.grid(True, linestyle='--', alpha=0.3)
        fig.tight_layout()
        
        # 标记预测数据
        if len(years) > len(df):
            plt.axvline(x=years[len(df)-1] + 0.5, color='gray', linestyle='--', alpha=0.7)
            plt.text(years[len(df)-1] + 0.6, max(market_sizes) * 0.5, '预测数据', 
                    rotation=90, verticalalignment='center', alpha=0.7)
        
        # 保存图表
        if save_fig:
            output_path = self.output_dir / f'bms_market_growth_{datetime.now().strftime("%Y%m%d")}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"已保存市场增长趋势图: {output_path}")
        
        plt.show()
    
    def plot_market_share(self, save_fig=True):
        """绘制市场份额饼图"""
        if not self.competitors:
            print("没有可用的竞争格局数据")
            return
        
        # 准备数据
        labels = list(self.competitors.keys())
        sizes = list(self.competitors.values())
        
        # 排序数据（由大到小）
        sorted_data = sorted(zip(labels, sizes), key=lambda x: x[1], reverse=True)
        labels, sizes = zip(*sorted_data)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 设置颜色映射
        cmap = plt.get_cmap('viridis')
        colors = [cmap(i/len(labels)) for i in range(len(labels))]
        
        # 突出显示主要玩家
        explode = [0.1 if i < 2 else 0 for i in range(len(labels))]
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=None, 
                                         autopct='%1.1f%%', startangle=90, 
                                         colors=colors, shadow=True)
        
        # 设置标签文本颜色
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
        
        # 添加图例
        ax.legend(wedges, labels, title="企业", loc="center left", 
                bbox_to_anchor=(1, 0, 0.5, 1))
        
        # 设置标题
        ax.set_title('BMS市场份额分布 (2024年)', fontsize=16, pad=20)
        
        # 等比例显示
        ax.axis('equal')  
        
        # 保存图表
        if save_fig:
            output_path = self.output_dir / f'bms_market_share_{datetime.now().strftime("%Y%m%d")}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"已保存市场份额图: {output_path}")
        
        plt.show()
    
    def create_interactive_dashboard(self):
        """创建交互式市场数据仪表板"""
        # 市场规模数据
        df_market = pd.DataFrame(self.market_data)
        
        # 预测未来数据
        if len(df_market) >= 2:
            last_year = df_market['year'].iloc[-1]
            last_size = df_market['market_size'].iloc[-1]
            last_growth = df_market['growth_rate'].iloc[-1] / 100 if df_market['growth_rate'].iloc[-1] else 0.25
            
            forecast_data = []
            for i in range(1, 3):
                next_year = last_year + i
                next_size = last_size * (1 + last_growth)
                forecast_data.append({
                    'year': next_year,
                    'market_size': next_size,
                    'growth_rate': last_growth * 100,
                    'is_forecast': True
                })
                last_size = next_size
            
            # 给原始数据添加标记
            df_market['is_forecast'] = False
            
            # 合并数据
            df_forecast = pd.DataFrame(forecast_data)
            df_market = pd.concat([df_market, df_forecast], ignore_index=True)
        
        # 竞争格局数据
        df_competitors = pd.DataFrame({
            'company': list(self.competitors.keys()),
            'market_share': list(self.competitors.values())
        }).sort_values('market_share', ascending=False)
        
        # 创建市场规模趋势图
        fig1 = go.Figure()
        
        # 添加实际数据柱状图
        fig1.add_trace(go.Bar(
            x=df_market[df_market['is_forecast'] == False]['year'],
            y=df_market[df_market['is_forecast'] == False]['market_size'],
            name='实际市场规模',
            marker_color='royalblue',
            text=df_market[df_market['is_forecast'] == False]['market_size'].apply(lambda x: f'{x:.1f}亿元'),
            textposition='auto'
        ))
        
        # 添加预测数据柱状图
        if 'is_forecast' in df_market.columns and any(df_market['is_forecast']):
            fig1.add_trace(go.Bar(
                x=df_market[df_market['is_forecast'] == True]['year'],
                y=df_market[df_market['is_forecast'] == True]['market_size'],
                name='预测市场规模',
                marker_color='rgba(65, 105, 225, 0.5)',
                text=df_market[df_market['is_forecast'] == True]['market_size'].apply(lambda x: f'{x:.1f}亿元'),
                textposition='auto'
            ))
        
        # 添加增长率曲线
        growth_data = df_market[df_market['growth_rate'].notna()]
        if not growth_data.empty:
            fig1.add_trace(go.Scatter(
                x=growth_data['year'],
                y=growth_data['growth_rate'],
                mode='lines+markers+text',
                name='同比增长率',
                yaxis='y2',
                line=dict(color='firebrick', width=2),
                marker=dict(size=8),
                text=growth_data['growth_rate'].apply(lambda x: f'{x:.1f}%'),
                textposition='top center'
            ))
        
        # 设置布局
        fig1.update_layout(
            title='BMS市场规模及增长趋势 (2023-2026)',
            xaxis=dict(title='年份'),
            yaxis=dict(title='市场规模 (亿元)'),
            yaxis2=dict(
                title='同比增长率 (%)',
                overlaying='y',
                side='right',
                range=[0, 40]
            ),
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified',
            barmode='group',
            template='plotly_white'
        )
        
        # 创建市场份额饼图
        fig2 = px.pie(
            df_competitors, 
            values='market_share', 
            names='company',
            title='BMS市场份额分布 (2024年)',
            hover_data=['market_share'],
            labels={'market_share': '市场份额 (%)'},
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        
        fig2.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>市场份额: %{value:.1f}%<extra></extra>"
        )
        
        # 保存图表到HTML文件
        output_path1 = self.output_dir / f'bms_market_trends_{datetime.now().strftime("%Y%m%d")}.html'
        output_path2 = self.output_dir / f'bms_market_share_{datetime.now().strftime("%Y%m%d")}.html'
        
        fig1.write_html(output_path1)
        fig2.write_html(output_path2)
        
        print(f"已生成交互式市场趋势图: {output_path1}")
        print(f"已生成交互式市场份额图: {output_path2}")
        
        # 创建综合仪表板
        dashboard = go.Figure()
        
        # 添加分析摘要
        dashboard.add_trace(go.Table(
            header=dict(
                values=["<b>指标</b>", "<b>2023</b>", "<b>2024</b>", "<b>变化</b>"],
                font=dict(size=14, color="white"),
                fill_color="royalblue",
                align="center"
            ),
            cells=dict(
                values=[
                    ["市场规模 (亿元)", "增长率 (%)", "市场集中度 (%)", "主导企业"],
                    [f"{df_market['market_size'].iloc[0]:.1f}", "N/A", "86.0", "宁德时代、弗迪时代"],
                    [f"{df_market['market_size'].iloc[1]:.1f}", f"{df_market['growth_rate'].iloc[1]:.1f}", "86.0", "宁德时代、弗迪时代"],
                    [f"↑ {df_market['market_size'].iloc[1] - df_market['market_size'].iloc[0]:.1f}", "N/A", "→", "→"]
                ],
                font=dict(size=13),
                fill_color=[["lavender", "white"] * 2],
                align="center"
            )
        ))
        
        dashboard.update_layout(
            title="BMS市场关键指标概览",
            height=200,
            margin=dict(l=10, r=10, t=50, b=10),
            template="plotly_white"
        )
        
        output_dashboard = self.output_dir / f'bms_market_dashboard_{datetime.now().strftime("%Y%m%d")}.html'
        dashboard.write_html(output_dashboard)
        
        print(f"已生成市场数据仪表板: {output_dashboard}")
        
        return output_path1, output_path2, output_dashboard
    
    def generate_report(self):
        """生成BMS市场分析报告和可视化"""
        print("开始生成BMS市场可视化报告...")
        
        # 生成静态图表
        self.plot_market_growth()
        self.plot_market_share()
        
        # 生成交互式仪表板
        trend_path, share_path, dashboard_path = self.create_interactive_dashboard()
        
        print("\n数据可视化生成完成！")
        print(f"请通过浏览器打开以下文件查看交互式报告:")
        print(f"- 市场趋势分析: {trend_path}")
        print(f"- 市场份额分析: {share_path}")
        print(f"- 市场综合仪表板: {dashboard_path}")
        
        # 返回生成的路径
        return {
            'trend_chart': trend_path,
            'share_chart': share_path,
            'dashboard': dashboard_path
        }

def main():
    parser = argparse.ArgumentParser(description='BMS市场数据可视化工具')
    parser.add_argument('--data', type=str, default='BMS市场分析报告.md', 
                        help='BMS市场数据文件路径(默认: "BMS市场分析报告.md")')
    args = parser.parse_args()
    
    # 创建可视化器并生成报告
    visualizer = BMSMarketVisualizer(args.data)
    visualizer.generate_report()

if __name__ == "__main__":
    main() 